# AI/ML ======================= api_key="93ed558e73cc4b5e8d145b83ef7ed670"

from flask import Flask, request, jsonify, render_template, send_from_directory
from openai import OpenAI
from db import Database  # Database interactions
import zipfile
import os

app = Flask(__name__)

# OpenAI client setup for generating tags
client = OpenAI(
    base_url="----",  # API base URL
    api_key="----" # API key
)

# Function to call GPT API for tag generation
def query_api(user_input):
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "First, generate useful topic tags as a comma-separated list. Then, generate a separate structured learning path in a clear numbered format. Do NOT mix them."},
            {"role": "user", "content": user_input},
            {"role": "assistant", "content": "Tags: [tag1, tag2, tag3]"},
            {"role": "assistant", "content": "Learning Path:\n1. Step One\n2. Step Two\n3. Step Three"}
        ]
    )
    content = response.choices[0].message.content

    print("Raw API Response:", content)  # Debugging output

    # Extract tags and learning path from API response
    tags = []
    learning_path = ""
    try:
        if "Tags:" in content and "Path:" in content:
            tags_section = content.split("Tags:")[1].split("Path:")[0].strip()
            learning_path = content.split("Path:")[1].strip()
            tags = [tag.strip() for tag in tags_section.split(",")]
        elif "Tags:" in content:
            tags_section = content.split("Tags:")[1].strip()
            tags = [tag.strip() for tag in tags_section.split(",")]
        elif "," in content:
            tags = [tag.strip() for tag in content.split(",")]
    except Exception as e:
        print("Error parsing the response:", str(e))

    return tags, learning_path

# Function to extract a course ZIP file from `Datasets`
def extract_zip(course_name):
    datasets_folder = "Datasets/"  # Folder where zip files are stored
    extracted_folder = f"courses/{course_name}"  # Destination folder

    # Ensure only ONE `.zip` extension
    zip_filename = f"{course_name.rstrip('.zip')}.zip"
    zip_path = os.path.join(datasets_folder, zip_filename)
    story_html_path = os.path.join(extracted_folder, "story.html")

    print(f"Looking for zip file: {zip_path}")  # Debugging
    print(f"Extracted folder should be: {extracted_folder}")  # Debugging

    if os.path.exists(zip_path):  # Ensure the zip file exists before extracting
        if not os.path.exists(extracted_folder):  # Extract only if needed
            try:
                with zipfile.ZipFile(zip_path, "r") as zip_ref:
                    zip_ref.extractall(extracted_folder)
                print(f"Extracted zip file to: {extracted_folder}")
            except Exception as e:
                print(f"Error extracting {zip_filename}: {e}")
                return None

        # Return path to `story.html` if it exists
        if os.path.exists(story_html_path):
            print(f"Found story.html at: {story_html_path}")
            return story_html_path
        else:
            print(f"story.html NOT found inside extracted folder!")
            return None
    else:
        print(f"Zip file not found: {zip_path}")
        return None

# Serve extracted course files like JS, CSS, and assets
@app.route("/courses/<course_name>/<path:file_path>")
def serve_course_files(course_name, file_path):
    extracted_folder = f"courses/{course_name}"
    return send_from_directory(extracted_folder, file_path)

# Main page route
@app.route("/")
def index():
    return render_template("index.html")

# Handle user query, generate tags, and find relevant courses
@app.route("/generate", methods=["POST"])
def generate():
    user_input = request.form.get("prompt")
    
    # Generate tags and learning path via GPT API
    tags, learning_path = query_api(user_input)

    # Search database for matching courses
    db = Database()
    matching_courses = db.select_tagsfiles(tags)

    # Generate file paths for matching courses
    courses = []
    for course in matching_courses:
        story_html_path = extract_zip(course[1])  # Extract zip if needed
        if story_html_path:
            courses.append({"name": course[1], "link": f"/{story_html_path}"})  # Correct `story.html` path
        else:
            print(f"Course found, but no extracted story.html: {course[1]}")

    print("Final learning path before sending:", learning_path)
    return jsonify({
        "tags": tags,
        "learning_path": learning_path,
        "courses": courses if courses else [{"name": "No relevant courses found.", "link": ""}]
    })

# Run Flask server in debug mode
if __name__ == "__main__":
    app.run(debug=True)
