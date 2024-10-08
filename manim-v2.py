import os
import shutil
from openai import OpenAI
import subprocess

# Set your OpenAI API key
os.getenv("OPENAI_API_KEY")
# Initialize the client
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
    return response

def save_code_to_file(code, filename):
    with open(filename, 'w') as f:
        f.write(code)

def run_manim_script(filename):
    command = ["manim", filename]
    result = subprocess.run(command, capture_output=True, text=True)
    return result

def find_and_move_video():
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
        destination = os.getcwd()
        shutil.move(video_file, destination)
        print(f"Video file moved to {destination}")
    else:
        print("No video file found.")

    # Delete the media directory
    if os.path.exists(media_dir):
        shutil.rmtree(media_dir)
        print("Media directory deleted.")

def main():
    topic = input("Enter the topic for the Manim animation: ")
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
        else:
            print("Animation generated and saved.")
            find_and_move_video()
    else:
        print("Animation generated and saved.")
        find_and_move_video()

if __name__ == "__main__":
    main()
