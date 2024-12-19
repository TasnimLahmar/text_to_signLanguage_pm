from nltk import word_tokenize
import useless_words
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import requests
import os
import subprocess
import shlex
from shutil import copyfile
from difflib import SequenceMatcher
from selenium import webdriver


# CONSTANTS
SIGN_PATH = "C:\\Users\\ASUS\\Desktop\\Signs"
DOWNLOAD_WAIT = 7
SIMILIARITY_RATIO = 0.9
# Get words

def download_word_sign(word):
    try:
        # Replace the executable_path with the path to your Firefox WebDriver executable
        browser = webdriver.Firefox()
    except Exception as e:
        print("Failed to initialize Firefox WebDriver:", e)
        return None

    try:
        # Replace "https://www.signasl.org/" with the actual URL of the website
        browser.get("https://www.signasl.org/")
    except Exception as e:
        print("Failed to open the website:", e)
        browser.quit()
        return None

    try:
        # Wait for the search field to be present on the page
        search_field = WebDriverWait(browser, 10).until(
            EC.presence_of_element_located((By.ID, "word"))  # Assuming the search field has an ID attribute
        )
        # Enter the word in the search field
        search_field.send_keys(word)
        search_field.send_keys(Keys.RETURN)  # Press Enter to perform the search
    except TimeoutException:
        print("Search field not found or timed out.")
        browser.quit()
        return None

    try:
        # Wait for the video container to be present on the page
        video = WebDriverWait(browser, 10).until(
            EC.presence_of_element_located((By.ID, "video_con_signasl_1"))
            # Assuming the first video container has this ID
        )

        # Get the source of the video from the source element inside the video tag
        source_elements = video.find_elements(By.TAG_NAME, "source")
        if source_elements:
            # Assuming the first source element contains the video source URL
            video_src = source_elements[0].get_attribute("src")
            print(video_src)
            if not video_src:
                print("Video source URL not found.")
                browser.quit()
                return None

            # Extract the file name from the URL
            file_name = os.path.basename(video_src)

            # Specify the path to save the video
            save_folder = "C:\\Users\\ASUS\\Desktop\\Signs"  # Specify the destination folder
            save_path = os.path.join(save_folder, file_name)

            # Download the video
            download_video(video_src, save_path)

            browser.close()
            return word
        else:
            print("No source elements found within the video tag.")
            return None
    except TimeoutException:
        print("Video container not found or timed out.")
        browser.quit()
        return None


def download_video(video_src, save_path):
    try:
        response = requests.get(video_src, stream=True)
        with open(save_path, 'wb') as file:
            for chunk in response.iter_content(chunk_size=1024):
                if chunk:
                    file.write(chunk)
        print("Download completed successfully.")
    except Exception as e:
        print("Failed to download video:", e)






def get_words_in_database():

    vids = os.listdir(SIGN_PATH)
    vid_names = [v[:-4] for v in vids]
    return vid_names

def process_text(text):
    # Split sentence into words
    words = word_tokenize(text)
    # Remove all meaningless words
    usefull_words = [str(w).lower() for w in words if w.lower() not in set(useless_words.words())]

    # TODO: Add stemming to words and change search accordingly. Ex: 'talking' will yield 'talk'.

    # TODO: Create Sytnax such that the words will be in ASL order as opposed to PSE.

    return usefull_words

def re_encode_video(input_file, output_file):
    # Re-encode the video with consistent properties
    command = f"ffmpeg -i {input_file} -c:v libx264 -preset medium -crf 23 -c:a aac -b:a 128k -vf scale=1920:1080 -r 30 {output_file}"
    args = shlex.split(command)
    process = subprocess.Popen(args)
    process.wait()
def is_video_reencoded(w, SIGN_PATH):
    encoded_path = SIGN_PATH + "\\" + w + ".mp4"
    return os.path.exists(encoded_path)



def merge_signs(words):
    print(words)
    for w in words:
        path = SIGN_PATH + "\\" + w + ".mp4"
        print(path)
    with open("vidlist.txt", 'w') as f:
        for w in words:
            f.write("file '" + SIGN_PATH + "\\" + w + ".mp4'\n")

    # Debug: Print the contents of vidlist.txt
    with open("vidlist.txt", 'r') as f:
        print("Contents of vidlist.txt:")
        print(f.read())

    command = "ffmpeg -f concat -safe 0 -i vidlist.txt -c copy output.mp4 -y"




    print("Executing FFmpeg command:", command)
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()
    print("FFmpeg command output:")
    print(stdout.decode())
    print("FFmpeg command errors:")
    print(stderr.decode())
    process.wait()


    if os.path.exists("output.mp4"):
        print("Output file 'output.mp4' exists.")
        # Copy the output file
        copyfile("output.mp4", SIGN_PATH + "\\Output\\outi.mp4")
        # remove the temporary file
        os.remove("output.mp4")
    else:
        print("Output file 'output.mp4' does not exist.")




def in_database(w):
    db_list = get_words_in_database()
    from nltk.stem import PorterStemmer
    ps = PorterStemmer()
    s = ps.stem(w)
    for word in db_list:
        if s == word[:len(s)]:
            return True
    return False


def similar(a, b):
    # Returns a decimal representing the similiarity between the two strings.
    return SequenceMatcher(None, a, b).ratio()

def find_in_db(w):
    best_score = -1.
    best_vid_name = None
    for v in get_words_in_database():
        s = similar(w, v)
        if best_score < s:
            best_score =  s
            best_vid_name = v
    if best_score > SIMILIARITY_RATIO:
        return best_vid_name
# Get text
text = str(input("Enter the text you would like to translate to sign language \n"))
#text = "no please"
print("Text: " + text)
# Process text
words = process_text(text)
# Download words that have not been downloaded in previous sessions.
real_words = []
for w in words:
    real_name = find_in_db(w)
    if real_name:
        print(w + " is already in db as " + real_name)
        real_words.append(real_name)
    else:
        real_words.append(download_word_sign(w))
words = real_words
# Concatenate videos and save output video to folder
merge_signs(words)

# Play the video
from os import startfile
startfile(SIGN_PATH + "\\Output\\outi.mp4")
