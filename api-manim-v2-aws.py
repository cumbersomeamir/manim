import os
import subprocess
import boto3
from flask import Flask, request, jsonify
from openai import OpenAI


app = Flask(__name__)

# Set your OpenAI and AWS credentials
aws_access_key = os.getenv("AWS_ACCESS_KEY")
aws_secret_key = os.getenv("AWS_SECRET_KEY")
s3_bucket_name = os.getenv("S3_BUCKET_NAME")
aws_region = os.getenv("AWS_REGION")

# Initialize the OpenAI client
client = OpenAI()

def generate_manim_code(topic):
    completion = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a super creative Python programmer specialized in the Manim library."},
            {"role": "user", "content": "Please write a Manim script that creates an animation about " + str(topic) + ". Provide only the code and nothing else no ```python or ``` only pure python code which will be executed"}
        ]
    )
    response = completion.choices[0].message.content
    print("The generated code is", response)
    return response

def generate_corrected_code(previous_code, error_message):
    completion = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a skilled Python programmer and debugger specialized in the Manim library."},
            {"role": "user", "content": f"The following Manim script has an error:\n\n{previous_code}\n\nThe error message is:\n\n{error_message}\n\nPlease provide a corrected version of the script. Provide only the code and nothing else no ```python or ``` only pure python code which will be executed"}
        ]
    )
    response = completion.choices[0].message.content
    print("The generated corrected code is", response)
    return response

def save_code_to_file(code, filename):
    with open(filename, 'w') as f:
        f.write(code)

def run_manim_script(filename):
    command = ["manim", filename]
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=120)
        print("Command stdout:", result.stdout)
        print("Command stderr:", result.stderr)
        print("The result is", result)
    except Exception as e:
        print(f"Error running Manim script: {str(e)}")
    return result

def find_video():
    media_dir = os.path.join(os.getcwd(), 'media')
    video_file = None
    for root, dirs, files in os.walk(media_dir):
        for file in files:
            if file.endswith('.mp4'):
                video_file = os.path.join(root, file)
                break
        if video_file:
            break
    if video_file:
        print(f"Video file found at {video_file}")
        return video_file
    else:
        print("No video file found.")
        return None

def upload_to_s3(file_path, file_name):
    s3_client = boto3.client('s3', 
                             aws_access_key_id=aws_access_key, 
                             aws_secret_access_key=aws_secret_key, 
                             region_name=aws_region)
    try:
        s3_client.upload_file(file_path, s3_bucket_name, file_name)
        s3_url = f"https://{s3_bucket_name}.s3.{aws_region}.amazonaws.com/{file_name}"
        print(f"File uploaded successfully. S3 URL: {s3_url}")
        return s3_url
    except Exception as e:
        print(f"Error uploading to S3: {str(e)}")
        return None

@app.route('/manim', methods=['POST'])
def video_story():
    data = request.get_json()
    topic = data.get('topic', '')
    code = generate_manim_code(topic)
    filename = "generated_manim.py"
    save_code_to_file(code, filename)
    result = run_manim_script(filename)

    if result.returncode != 0:
        error_message = result.stderr
        corrected_code = generate_corrected_code(code, error_message)
        save_code_to_file(corrected_code, filename)
        result = run_manim_script(filename)
        if result.returncode != 0:
            print("An error occurred again. Could not fix the script automatically.")
            return jsonify({'status': 'error', 'message': 'Could not generate animation.'}), 500

    video_file_path = find_video()

    if video_file_path:
        video_file_name = os.path.basename(video_file_path)
        s3_url = upload_to_s3(video_file_path, video_file_name)
        if s3_url:
            return jsonify({'status': 'success', 'url': s3_url})
        else:
            return jsonify({'status': 'error', 'message': 'Failed to upload video to S3.'}), 500
    else:
        return jsonify({'status': 'error', 'message': 'Video file not found.'}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=7005, use_reloader=False)
