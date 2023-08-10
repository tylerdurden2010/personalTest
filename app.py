import random
import string
from flask import Flask, send_file, make_response
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
from flask import Flask, request, render_template
import pymysql

app = Flask(__name__)

def generate_captcha_text(length=4):
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))


def generate_captcha_image(captcha_text, font_path='arial.ttf', font_size=36, spacing=10):
    font = ImageFont.truetype(font_path, font_size)

    # Function to apply rotation to a single character image
    def distort_char_image(char_image):
        angle = random.uniform(-30, 30)
        char_image = char_image.rotate(angle, resample=Image.BICUBIC, expand=True)
        return char_image

    # Calculate the width and height of each character
    dummy_image = Image.new('RGBA', (1, 1), color=(255, 255, 255, 0))
    draw = ImageDraw.Draw(dummy_image)
    char_sizes = [draw.textsize(char, font=font) for char in captcha_text]

    # Adjust the spacing between characters
    spacings = [spacing] * (len(captcha_text) - 1)
    random_index = random.randint(0, len(spacings) - 1)
    spacings[random_index] = -spacing // 2

    width = sum(w for w, _ in char_sizes) + sum(spacings)
    height = max(h for _, h in char_sizes) + 10

    image = Image.new('RGBA', (width, height), color=(255, 255, 255, 0))
    
    x_offset = 0

    # Draw and distort each character
    for index, char in enumerate(captcha_text[:-1]):
        char_width, char_height = char_sizes[index]
        char_image = Image.new('RGBA', (char_width, char_height), color=(255, 255, 255, 0))
        char_draw = ImageDraw.Draw(char_image)
        char_draw.text((0, 0), char, font=font, fill='black')
        char_image = distort_char_image(char_image)
        image.paste(char_image, (x_offset, (height - char_image.height) // 2), char_image)
        x_offset += char_width + spacings[index]

    # Draw and distort the last character
    char_width, char_height = char_sizes[-1]
    char_image = Image.new('RGBA', (char_width, char_height), color=(255, 255, 255, 0))
    char_draw = ImageDraw.Draw(char_image)
    char_draw.text((0, 0), captcha_text[-1], font=font, fill='black')
    char_image = distort_char_image(char_image)
    image.paste(char_image, (x_offset, (height - char_image.height) // 2), char_image)

    # Convert the image to RGB mode to remove the alpha channel
    image = image.convert('RGB')

    # Add lines
    num_lines = 4
    for _ in range(num_lines):
        start_x = random.randint(0, width)
        start_y = random.randint(0, height)
        end_x = random.randint(0, width)
        end_y = random.randint(0, height)
        ImageDraw.Draw(image).line([(start_x, start_y), (end_x, end_y)], fill='black', width=2)

    # Add noise
    num_noise_dots = 150
    for _ in range(num_noise_dots):
        x = random.randint(0, width)
        y = random.randint(0, height)
        ImageDraw.Draw(image).point((x, y), fill='black')

    image_bytes = BytesIO()
    image.save(image_bytes, format='PNG')
    image_bytes.seek(0)

    return image_bytes

@app.route('/generate_captcha', methods=['GET'])
def generate_captcha():
    captcha_text = generate_captcha_text()
    captcha_image = generate_captcha_image(captcha_text)
    response = make_response(send_file(captcha_image, mimetype='image/png'))
    # response.headers['Captcha-Text'] = captcha_text
    return response


@app.route('/test')
def test():
    return 'Hello, this is a test!'


# For demonstration purposes, we're using a MariaDB (MySQL) database
DB_HOST = 'localhost'
DB_USER = 'your_db_user'
DB_PASSWORD = 'your_db_password'
DB_NAME = 'insecure_db'

def initialize_database():
    conn = pymysql.connect(host=DB_HOST, user=DB_USER, password=DB_PASSWORD)
    cursor = conn.cursor()

    cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME}")
    cursor.execute(f"USE {DB_NAME}")

    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                      id INT AUTO_INCREMENT PRIMARY KEY,
                      username VARCHAR(50),
                      password VARCHAR(50))''')
    cursor.execute("INSERT INTO users (username, password) VALUES (%s, %s)", ('admin', 'admin123'))

    conn.commit()
    conn.close()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']

    conn = pymysql.connect(host=DB_HOST, user=DB_USER, password=DB_PASSWORD, db=DB_NAME)
    cursor = conn.cursor()

    # This is where the vulnerability lies
    query = "SELECT * FROM users WHERE username = '%s' AND password = '%s'" % (username, password)

    cursor.execute(query)
    user = cursor.fetchone()
    conn.close()

    if user:
        return "Login successful!"
    else:
        return "Login failed!"



if __name__ == '__main__':
    initialize_database()
    app.run(host='0.0.0.0', port=5000)

