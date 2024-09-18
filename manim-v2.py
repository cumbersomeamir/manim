import os
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
        {"role": "user", "content": "Please write a Manim script that creates an animation about " + str(topic) + ". Provide only the code without any explanations."}
      ]
    )
    return completion['choices'][0]['message']['content']

def generate_corrected_code(previous_code, error_message):
    completion = client.chat.completions.create(
      model="gpt-4o",
      messages=[
        {"role": "system", "content": "You are a skilled Python programmer and debugger specialized in the Manim library."},
        {"role": "user", "content": f"The following Manim script has an error:\n\n{previous_code}\n\nThe error message is:\n\n{error_message}\n\nPlease provide a corrected version of the script. Provide only the corrected code without any explanations."}
      ]
    )
    return completion['choices'][0]['message']['content']

def save_code_to_file(code, filename):
    with open(filename, 'w') as f:
        f.write(code)

def run_manim_script(filename):
    command = ["manim", filename]
    result = subprocess.run(command, capture_output=True, text=True)
    return result

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
    else:
        print("Animation generated and saved.")

if __name__ == "__main__":
    main()
