from flask import Flask, render_template , request , send_file 
from PIL import Image , ImageOps
import io , random , string , os  
from gtts import gTTS
import numpy as np , cv2 
from fpdf import FPDF

app = Flask(__name__)


@app.route('/')
def text():
    return render_template('text_tools.html')

@app.route('/image')
def image():  
    return render_template('image_tools.html')

@app.route('/security')
def security():
    return render_template('security_tools.html')

def sentence_case(text):
    sentences = text.split('. ')
    return '. '.join(s.capitalize() for s in sentences)

# ------------------------------------image-tools-------------------------------------------------------

# ---------- Image Resizer ----------
@app.route('/image-resizer', methods=['POST'])
def image_resizer():
    if 'image_file' not in request.files:
        return "No image uploaded", 400

    try:
        image = Image.open(request.files['image_file'])
        image = ImageOps.exif_transpose(image)

        width = int(request.form.get('width'))
        height = int(request.form.get('height'))
        resized = image.resize((width, height))

        img_io = io.BytesIO()
        resized.save(img_io, format='PNG')
        img_io.seek(0)
        return send_file(img_io, mimetype='image/png', as_attachment=True, download_name='resized.png')
    except Exception as e:
        return f"Error resizing image: {e}", 500


# ---------- Aspect Ratio Fixer ----------
@app.route('/ratio-fixer', methods=['POST'])
def ratio_fixer():
    if 'image_file' not in request.files:
        return "No image uploaded", 400

    try:
        image = Image.open(request.files['image_file'])
        image = ImageOps.exif_transpose(image)

        aspect_ratio = request.form.get('aspect_ratio')
        ratios = {'1:1': 1, '16:9': 16 / 9, '4:3': 4 / 3}
        target = ratios.get(aspect_ratio)

        if not target:
            return "Invalid aspect ratio", 400

        width, height = image.size
        current_ratio = width / height

        if current_ratio > target:
            new_width = int(height * target)
            offset = (width - new_width) // 2
            cropped = image.crop((offset, 0, offset + new_width, height))
        else:
            new_height = int(width / target)
            offset = (height - new_height) // 2
            cropped = image.crop((0, offset, width, offset + new_height))

        img_io = io.BytesIO()
        cropped.save(img_io, format='PNG')
        img_io.seek(0)
        return send_file(img_io, mimetype='image/png', as_attachment=True, download_name='aspect_fixed.png')
    except Exception as e:
        return f"Error fixing ratio: {e}", 500


# ---------- Face Blur Tool ----------
@app.route('/face-blur', methods=['POST'])
def face_blur():
    if 'image_file' not in request.files:
        return "No image uploaded", 400

    try:
        image = Image.open(request.files['image_file'])
        image = ImageOps.exif_transpose(image)

        open_cv_image = np.array(image.convert('RGB'))[:, :, ::-1].copy()
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        gray = cv2.cvtColor(open_cv_image, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.1, 4)

        for (x, y, w, h) in faces:
            face = open_cv_image[y:y+h, x:x+w]
            blurred = cv2.blur(face, (25, 25))
            open_cv_image[y:y+h, x:x+w] = blurred

        result_img = Image.fromarray(cv2.cvtColor(open_cv_image, cv2.COLOR_BGR2RGB))
        img_io = io.BytesIO()
        result_img.save(img_io, format='PNG')
        img_io.seek(0)
        return send_file(img_io, mimetype='image/png', as_attachment=True, download_name='face_blurred.png')
    except Exception as e:
        return f"Error blurring face: {e}", 500



# -------------------------------security-tools-------------------------------------------------------


#----------PASSWORD CHECKER---------#
@app.route('/check-password', methods=['POST'])
def check_password():
    password = request.form.get('passwordInput', '')
    
    strength = "Weak"
    if len(password) >= 12 and any(c.isupper() for c in password) \
       and any(c.islower() for c in password) and any(c.isdigit() for c in password) \
       and any(c in "!@#$%^&*()-_=+[{]}\\|;:'\",<.>/?`~" for c in password):
        strength = "Very Strong"
    elif len(password) >= 8:
        strength = "Moderate"

    return render_template('security_tools.html', strength=strength)

#-------------PASSWORD GENERATOR---------#


@app.route('/generate-password', methods=['POST'])
def generate_password():
    length = int(request.form.get('length', 12))
    include_upper = 'includeUpper' in request.form
    include_numbers = 'includeNumbers' in request.form
    include_symbols = 'includeSymbols' in request.form

    characters = list(string.ascii_lowercase)
    if include_upper:
        characters += list(string.ascii_uppercase)
    if include_numbers:
        characters += list(string.digits)
    if include_symbols:
        characters += list('!@#$%^&*()-_=+[{]}\\|;:\'",<.>/?`~')

    if not characters:
        generated_password = "Error: Select at least one character type."
    else:
        generated_password = ''.join(random.choices(characters, k=length))

    return render_template('security_tools.html', generated_password=generated_password)


# ------------------------------------text-tools-------------------------------------------------------




# ---------------- CASE CONVERTOR ------------------


@app.route('/case_convert', methods=['POST'])
def case_convert():
    input__text = request.form.get('case__input', '')
    action = request.form.get('action')
    converted__text = ""

    if action == 'upper':
        converted__text = input__text.upper()
    elif action == 'lower':
        converted__text = input__text.lower()
    elif action == 'sentence':
        converted__text = sentence_case(input__text)

    return render_template('text_tools.html',
                           input__text=input__text,
                           converted__text=converted__text)


# ---------------- WORD COUNTER ------------------
@app.route('/word_count', methods=['POST'])
def word_count():
    input = request.form.get('count_input', '')
    word_count = len(input.split())
    char_count = len(input)
    sentence_count = input.count('.') + input.count('!') + input.count('?')

    return render_template('text_tools.html',
                           input_text=input,
                           word_count=word_count,
                           char_count=char_count,
                           sentence_count=sentence_count)


# ---------------- TEXT TO SPEECH ------------------
@app.route('/text_speech', methods=['POST'])
def text_speech():
    tts_text = request.form.get('tts_input')
    tts_audio = ""

    if tts_text.strip():
        tts = gTTS(tts_text)
        audio_path = "static/audio/output.mp3"
        tts.save(audio_path)
        tts_audio = 'audio/output.mp3'

    return render_template('text_tools.html',
                           tts_text=tts_text,
                           tts_audio=tts_audio)


# ---------------- REMOVE DUPLICATES ------------------


@app.route('/remove-duplicates', methods=['GET', 'POST'])
def remove_duplicates():
    input_text = request.form.get('input_txt', '') if request.method == 'POST' else ''
    output_text = ''
    
    if request.method == 'POST' and input_text:
        seen_lines = set()
        processed_lines = []
        
        for line in input_text.splitlines():
            words = line.split()
            unique_words = []
            previous_word = None
            
            for word in words:
                if word != previous_word:  
                    unique_words.append(word)
                    previous_word = word
            
            processed_line = ' '.join(unique_words)
            
            if processed_line not in seen_lines:
                processed_lines.append(processed_line)
                seen_lines.add(processed_line)
            elif not processed_line.strip(): 
                processed_lines.append(processed_line)
        
        output_text = '\n'.join(processed_lines)
    
    return render_template('text_tools.html',
                         input_txt=input_text,
                         output_text=output_text)

# ---------------- text to PDF ------------------


@app.route('/text-to-pdf', methods=['GET', 'POST'])
def text_to_pdf():
    if request.method == 'POST':
        text = request.form['text_input']

        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)

        for line in text.split('\n'):
            pdf.multi_cell(0, 10, line)

        pdf_bytes = pdf.output(dest='S').encode('latin1')

        pdf_output = io.BytesIO(pdf_bytes)
        pdf_output.seek(0)

        return send_file(pdf_output, as_attachment=True, download_name="converted.pdf", mimetype='application/pdf')

    return render_template('text_tools.html')


if __name__ == '__main__':
    app.run(debug=True)
