import tkinter as tk
from PIL import Image, ImageTk, ImageDraw
import time
import os
import shutil
import pygame
import json
import subprocess
import requests
import zipfile
import winreg
import re
import threading
import asyncio
import aiohttp
import aiofiles
import aioshutil
from pathlib import Path

progress_bar = None
progress_text = None
download_progress = 0
button_text = None
is_processing = False
launch_canvas = None
progress_fill = None
is_download_complete = False
is_game_launched = False

def update_progress_bar_indeterminate(canvas):
    canvas.move(progress_fill, 10, 0)
    canvas.update_idletasks()

def create_progress_bar(canvas):
    global progress_bar, progress_text, progress_fill
    bar_width = 450
    bar_height = 30
    x = (1280 - bar_width) // 2
    y = 575
    progress_bar = canvas.create_rectangle(x, y, x + bar_width, y + bar_height, fill='#141414', outline='#dbc7a2', width=2, state='hidden')
    progress_fill = canvas.create_rectangle(x + 2, y + 2, x + 2, y + bar_height - 2, fill='#780606', width=0, state='hidden')
    progress_text = canvas.create_text(x + bar_width // 2, y + bar_height // 2, text="0%", fill="#FFFFFF", font=("Faustina Regular", 14), state='hidden')

def update_progress_bar(canvas, progress_fill, progress):
    if progress_bar is not None:
        bar_width = 446
        if progress is not None:
            fill_width = int(bar_width * progress)
            canvas.coords(progress_fill, 417, 577, 417 + fill_width, 603)
            canvas.itemconfig(progress_text, text=f"{int(progress * 100)}%")
        else:
            print("random progress")
        canvas.update_idletasks()

async def download_and_install():
    global download_progress, is_processing
    
    download_progress = 0.95
    launch_game()
    download_progress = 1.0
    await asyncio.sleep(5)
    is_processing = False
    hide_progress_bar()

def hide_progress_bar():
    global progress_bar, progress_text, progress_fill
    if progress_bar is not None:
        launch_canvas.itemconfig(progress_bar, state='hidden')
        launch_canvas.itemconfig(progress_fill, state='hidden')
        launch_canvas.itemconfig(progress_text, state='hidden')

async def extract_zip(zip_path, extract_to):
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, zipfile.ZipFile(zip_path).extractall, extract_to)

async def download_file(session, url, filename):
    async with session.get(url) as response:
        if response.status != 200:
            print(f"{response.status} {url}")
            return
        total_size = int(response.headers.get('content-length', 0))
        if total_size == 0:
            print("c-l")
            total_size = None
        downloaded = 0
        async with aiofiles.open(filename, 'wb') as f:
            async for chunk in response.content.iter_chunked(8192):
                await f.write(chunk)
                downloaded += len(chunk)
                if total_size:
                    yield downloaded / total_size
                else:
                    yield None

async def copy_file(src, dst):
    async with aiofiles.open(src, 'rb') as fsrc:
        async with aiofiles.open(dst, 'wb') as fdst:
            await fdst.write(await fsrc.read())

async def copy_folder(src, dst):
    await aioshutil.copytree(src, dst, dirs_exist_ok=True)

def launch_game():
    global download_progress, is_processing, is_download_complete
    game_exe = os.path.join(target_directory, "Game.exe")
    try:
        process = subprocess.Popen(game_exe)
        is_processing = False
        is_download_complete = True
        root.after(5000, hide_progress_bar)
    except Exception as e:
        print(f"{str(e)}")

async def download_and_install():
    global download_progress, is_processing, is_download_complete, is_game_launched
    temp_dir = os.path.join(base_directory, "temp")
    zip_path = os.path.join(temp_dir, "repo.zip")

    try:
        os.makedirs(temp_dir, exist_ok=True)
        
        async with aiohttp.ClientSession() as session:
            async for progress in download_file(session, repo_zip_url, zip_path):
                if progress is not None:
                    download_progress = progress * 0.3
                else:
                    print("random progress c-l")
        
        print(f"{os.path.getsize(zip_path)}")

        await extract_zip(zip_path, temp_dir)
        download_progress = 0.4

        if os.path.exists(target_directory):
            shutil.rmtree(target_directory)
        os.makedirs(target_directory, exist_ok=True)

        files_to_copy = [
            "credits.html", "d3dcompiler_47.dll", "debug.log", "ffmpeg.dll", "Game.exe",
            "icudtl.dat", "libEGL.dll", "libGLESv2.dll", "natives_blob.bin", "node.dll",
            "nw.dll", "nw_100_percent.pak", "nw_200_percent.pak", "nw_elf.dll", "package.json",
            "resources.pak", "snapshot_blob.bin"
        ]
        folders_to_copy = ['tools', 'locales', 'swiftshader']

        total_items = len(files_to_copy) + len(folders_to_copy)
        for i, file in enumerate(files_to_copy):
            source_file = os.path.join(base_directory, file)
            target_file = os.path.join(target_directory, file)
            if os.path.exists(source_file):
                await copy_file(source_file, target_file)
            else:
                print(f"404 {source_file}")
            download_progress = 0.4 + ((i + 1) / total_items) * 0.5

        for i, folder in enumerate(folders_to_copy):
            source_folder = os.path.join(base_directory, folder)
            target_folder = os.path.join(target_directory, folder)
            if os.path.exists(source_folder):
                await copy_folder(source_folder, target_folder)
            else:
                print(f"404 {source_folder}")
            download_progress = 0.9 + ((i + 1) / len(folders_to_copy)) * 0.05

        extracted_repo_folder = os.path.join(temp_dir, 'main')
        if os.path.exists(extracted_repo_folder):
            await copy_folder(extracted_repo_folder, target_directory)
        else:
            print(f"404 {extracted_repo_folder}")

        download_progress = 0.95
        launch_game()
        download_progress = 1.0
        is_download_complete = True
        is_game_launched = True
    finally:
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
        is_processing = False

def start_async_download():
    asyncio.run(download_and_install())

def update_button_text(text):
    global button_text
    button_canvas.itemconfig(button_text, text=text)
    button_canvas.update_idletasks()

def update_button_text(text):
    global button_text
    button_canvas.itemconfig(button_text, text=text)
    button_canvas.update_idletasks()

def show_progress_bar():
    launch_canvas.itemconfig(progress_bar, state='normal')
    launch_canvas.itemconfig(progress_fill, state='normal')
    launch_canvas.itemconfig(progress_text, state='normal')

def show_frame(frame):
    frame.tkraise()
    if frame == launch_frame:
        if progress_bar is not None:
            launch_canvas.itemconfig(progress_bar, state='normal')
            launch_canvas.itemconfig(progress_fill, state='normal')
            launch_canvas.itemconfig(progress_text, state='normal')
        if is_processing:
            update_ui()

def set_permissions(path):
    if os.path.isfile(path):
        os.chmod(path, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)
    elif os.path.isdir(path):
        for root, dirs, files in os.walk(path):
            for name in dirs:
                os.chmod(os.path.join(root, name), stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)
            for name in files:
                os.chmod(os.path.join(root, name), stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)

def load_gif(file_path):
    gif = Image.open(file_path)
    frames = []
    try:
        while True:
            frame = gif.copy()
            frame = resize_image(frame, 1280, 720)
            frames.append(frame)
            gif.seek(gif.tell() + 1)
    except EOFError:
        pass
    return frames

def animate_gif(canvas, frames, delay=100):
    def update_frame(index):
        frame = ImageTk.PhotoImage(frames[index])
        canvas.delete("gif")
        canvas.create_image(0, 0, image=frame, anchor="nw", tags="gif")
        canvas.image = frame
        create_sidebar(canvas, frames[index], credits_frame)
        draw_credits_elements(canvas)
        canvas.after_id = canvas.after(delay, update_frame, (index + 1) % len(frames))
    update_frame(0)

def fade_to_black_and_show_frame(target_frame, new_target_image):
    global current_canvas, current_image, target_canvas, target_image

    target_canvas = get_canvas_for_frame(target_frame)
    target_image = new_target_image
    
    if current_canvas == launch_canvas:
        button_canvas.place_forget()

    if current_canvas == credits_canvas:
        current_canvas.after_cancel(credits_canvas.after_id)
    
    if isinstance(target_image, list):
        target_image = target_image[0]

    if isinstance(current_image, list):
        current_image = current_image[0]

    blend_images(current_image, target_image, current_canvas, target_canvas, target_frame)
    
    current_canvas = target_canvas
    current_image = new_target_image

    if target_frame == credits_frame and isinstance(new_target_image, list):
        animate_gif(target_canvas, new_target_image)
    if target_frame == launch_frame:
        show_progress_bar()

def blend_images(img1, img2, canvas1, canvas2, target_frame):
    canvas1.delete("all")

    if isinstance(img1, (list, tuple)):
        img1 = img1[0]
    if isinstance(img2, (list, tuple)):
        img2 = img2[0]
    
    if isinstance(img1, ImageTk.PhotoImage):
        img1 = ImageTk.getimage(img1)
    if isinstance(img2, ImageTk.PhotoImage):
        img2 = ImageTk.getimage(img2)

    img1 = img1.convert("RGBA")
    img2 = img2.convert("RGBA")
    
    steps = 5
    for i in range(steps + 1):
        alpha = i / steps
        blended_img = Image.blend(img1, img2, alpha)
        blended_photo = ImageTk.PhotoImage(blended_img)

        canvas1.delete("transition")
        canvas1.create_image(0, 0, image=blended_photo, anchor="nw", tags="transition")
        canvas1.image = blended_photo

        create_sidebar(canvas1, blended_img, target_frame)

        root.update()
        time.sleep(0.01)

    show_frame(target_frame)

    if isinstance(current_image, (list, tuple)):
        animate_gif(canvas2, current_image)
    else:
        final_photo = ImageTk.PhotoImage(img2)
        canvas2.delete("all")
        canvas2.create_image(0, 0, image=final_photo, anchor="nw")
        canvas2.image = final_photo
        create_sidebar(canvas2, img2, target_frame)
    
    if target_frame == settings_frame:
        draw_settings_elements()
    elif target_frame == credits_frame:
        draw_credits_elements(credits_canvas)
    elif target_frame == launch_frame:
        button_canvas.place(relx=0.5, rely=1.0, anchor="s", y=-15)
        show_progress_bar()
        
def resize_image(image, max_width, max_height):
    width, height = image.size
    aspect_ratio = width / height

    if width > max_width or height > max_height:
        if width / max_width > height / max_height:
            new_width = max_width
            new_height = int(max_width / aspect_ratio)
        else:
            new_height = max_height
            new_width = int(max_height * aspect_ratio)
        return image.resize((new_width, new_height), Image.LANCZOS)
    return image

def center_image_on_canvas(canvas, image):
    canvas_width = canvas.winfo_width()
    canvas_height = canvas.winfo_height()
    img_width, img_height = image.size

    x_offset = (canvas_width - img_width) // 2
    y_offset = (canvas_height - img_height) // 2
    return x_offset, y_offset

def get_canvas_for_frame(frame):
    if frame == launch_frame:
        return launch_canvas
    elif frame == settings_frame:
        return settings_canvas
    elif frame == credits_frame:
        return credits_canvas

def create_diamond(canvas, x, y, size, fill, outline="", tags=None):
    points = [
        x, y - size / 2,
        x + size / 2, y,
        x, y + size / 2,
        x - size / 2, y,
    ]
    return canvas.create_polygon(points, fill=fill, outline=outline, tags=tags)

def create_sidebar(canvas, main_image, current_frame, button_width=190):
    if isinstance(main_image, list):
        main_image = main_image[0]
        
    main_photo = ImageTk.PhotoImage(main_image)

    BUTTON_WIDTH_LAUNCH = 201
    BUTTON_WIDTH_SETTINGS = 211
    BUTTON_WIDTH_CREDITS = 221

    sidebar_image = Image.new('RGBA', (300, 720), (0, 0, 0, 0))
    draw = ImageDraw.Draw(sidebar_image)
    
    draw.polygon([(0, 0), (120, 0), (230, 720), (0, 720)], fill=(20, 20, 20, 200))
    
    sidebar_photo = ImageTk.PhotoImage(sidebar_image)
    
    main_photo = ImageTk.PhotoImage(main_image)
    canvas.create_image(0, 0, image=main_photo, anchor="nw")
    canvas.image = main_photo
    
    canvas.create_image(0, 0, image=sidebar_photo, anchor="nw")
    canvas.sidebar_image = sidebar_photo

    create_diagonal_button(canvas, 480, "Launch", lambda: fade_to_black_and_show_frame(launch_frame, launch_image), current_frame == launch_frame, BUTTON_WIDTH_LAUNCH)
    create_diagonal_button(canvas, 540, "Settings", lambda: fade_to_black_and_show_frame(settings_frame, settings_image), current_frame == settings_frame, BUTTON_WIDTH_SETTINGS)
    create_diagonal_button(canvas, 600, "Credits", lambda: fade_to_black_and_show_frame(credits_frame, credits_image), current_frame == credits_frame, BUTTON_WIDTH_CREDITS)

def create_diagonal_button(canvas, y, text, command, is_current, button_width=190):
    x1, y1 = 0, y
    x2, y2 = x1 + button_width, y1 + 40
    
    fill_color = '#141414' if not is_current else '#780606'
    button = canvas.create_polygon(
        [(x1, y1), (x2, y1), (x2+20, y2), (x1, y2)], 
        fill=fill_color, outline='', width=0, stipple='gray50'
    )
    text_item = canvas.create_text(
        (x1 + x2) / 2, 
        (y1 + y2) / 2, 
        text=text, 
        fill='white', 
        font=("Faustina Regular", 14)
    )
    
    canvas.tag_bind(button, '<Button-1>', lambda e: command())
    canvas.tag_bind(text_item, '<Button-1>', lambda e: command())

def create_mute_button(canvas, y, x):
    button_width = 100
    button_height = 40
    y = y - 13

    points = [
        x, y - 5,
        x + button_width, y - 5,
        x + button_width + 15, y + button_height + 5,
        x + 15, y + button_height + 5
    ]

    button = canvas.create_polygon(
        points, 
        fill='#141414', 
        outline='', 
        width=0, 
        stipple='gray50',
        tags="settings_elements"
    )
    
    is_muted = load_mute_state()
    text = "Unmute" if is_muted else "Mute"
    text_item = canvas.create_text(
        x + button_width / 1.74, 
        y + button_height / 2.2, 
        text=text, 
        fill='white', 
        font=("Faustina Regular", 14),
        tags="settings_elements"
    )
    
    canvas.tag_bind(button, '<Button-1>', lambda e: toggle_mute_and_update(canvas))
    canvas.tag_bind(text_item, '<Button-1>', lambda e: toggle_mute_and_update(canvas))

def load_mute_state():
    config = load_config()
    return config['is_muted']

def draw_settings_elements():
    settings_canvas.delete("settings_elements")
    settings_label = settings_canvas.create_text(640, 50, text="Settings Menu", font=("Faustina Regular", 24), fill="white", tags="settings_elements")
    volume_label = settings_canvas.create_text(640, 105, text="Background music volume:", font=("Faustina Regular", 18), fill="white", tags="settings_elements")
    create_volume_controls(settings_canvas, 140)

def toggle_mute():
    config = load_config()
    is_muted = not config['is_muted']
    if is_muted:
        pygame.mixer.music.pause()
    else:
        pygame.mixer.music.unpause()
    save_mute_state(is_muted)
    pygame.mixer.music.set_volume(config['volume'] if not is_muted else 0)

def toggle_mute_and_update(canvas):
    toggle_mute()
    draw_settings_elements()

def create_volume_controls(canvas, y):
    global volume_text, volume_cursor
    slider_width = 300
    slider_height = 10
    canvas_width = canvas.winfo_width()
    x = (canvas_width - slider_width) // 2

    canvas.create_rectangle(x, y, x + slider_width, y + slider_height, 
                            fill='#141414', outline='', width=0, stipple='gray50',
                            tags="settings_elements")
    
    cursor_size = 20
    current_volume = load_volume()
    cursor_x = x + (slider_width - cursor_size) * current_volume
    
    volume_cursor = create_diamond(canvas, cursor_x + cursor_size/2, y + slider_height/2, cursor_size, 
                                   fill='#780606', outline='', tags="settings_elements")
    
    volume_text = canvas.create_text(x - 40, y + slider_height/2, text=f"{int(current_volume * 100)}%", 
                                     fill="white", font=("Faustina Regular", 12), tags="settings_elements")
    
    create_mute_button(canvas, y, x + slider_width + 20)

    def update_volume(event):
        if not load_mute_state():
            x_local = event.x - x
            volume = max(0, min(1, x_local / slider_width))
            pygame.mixer.music.set_volume(volume)
            new_x = x + max(0, min(slider_width - cursor_size, x_local))
            canvas.coords(volume_cursor, 
                        new_x + cursor_size/2, y + slider_height/2 - cursor_size/2,
                        new_x + cursor_size, y + slider_height/2,
                        new_x + cursor_size/2, y + slider_height/2 + cursor_size/2,
                        new_x, y + slider_height/2)
            canvas.itemconfig(volume_text, text=f"{int(volume * 100)}%")
            save_volume(volume)
    
    canvas.tag_bind(volume_cursor, '<B1-Motion>', update_volume)
    canvas.tag_bind(volume_cursor, '<Button-1>', update_volume)

def create_volume_slider(canvas, y):
    global volume_text, volume_cursor
    slider_width = 300
    slider_height = 10
    x = 230
    canvas.create_rectangle(x, y, x + slider_width, y + slider_height, 
                            fill='#141414', outline='', width=0, stipple='gray50',
                            tags="settings_elements")
    
    cursor_size = 20
    current_volume = load_volume()
    cursor_x = x + (slider_width - cursor_size) * current_volume
    
    volume_cursor = create_diamond(canvas, cursor_x + cursor_size/2, y + slider_height/2, cursor_size, 
                                   fill='#780606', outline='', tags="settings_elements")
    
    volume_text = canvas.create_text(x - 40, y + slider_height/2, text=f"{int(current_volume * 100)}%", 
                                     fill="white", font=("Faustina Regular", 12), tags="settings_elements")
    
    def update_volume(event):
        if not load_mute_state():
            x_local = event.x - x
            volume = max(0, min(1, x_local / slider_width))
            pygame.mixer.music.set_volume(volume)
            new_x = x + max(0, min(slider_width - cursor_size, x_local))
            canvas.coords(volume_cursor, 
                        new_x + cursor_size/2, y + slider_height/2 - cursor_size/2,
                        new_x + cursor_size, y + slider_height/2,
                        new_x + cursor_size/2, y + slider_height/2 + cursor_size/2,
                        new_x, y + slider_height/2)
            canvas.itemconfig(volume_text, text=f"{int(volume * 100)}%")
            save_volume(volume)

    
    canvas.tag_bind(volume_cursor, '<B1-Motion>', update_volume)
    canvas.tag_bind(volume_cursor, '<Button-1>', update_volume)

def ensure_config_directory():
    config_dir = get_config_directory()
    if not os.path.exists(config_dir):
        os.makedirs(config_dir)

def initialize_audio():
    config = load_config()
    volume = config['volume']
    is_muted = config['is_muted']
    
    pygame.mixer.init()
    pygame.mixer.music.load("assets/launchermusic.ogg")
    pygame.mixer.music.set_volume(volume if not is_muted else 0)
    
    if not is_muted:
        pygame.mixer.music.play(-1)
    
    return is_muted

def get_config_directory():
    appdata_roaming = os.getenv('APPDATA')
    return os.path.join(appdata_roaming, 'CoffinLauncher')

def get_config_path():
    return os.path.join(get_config_directory(), 'config.json')

def create_default_config():
    return {'volume': 0.5, 'is_muted': False}

def save_config(config):
    ensure_config_directory()
    config_path = get_config_path()
    with open(config_path, 'w') as f:
        json.dump(config, f)

def save_volume(volume):
    config = load_config()
    config['volume'] = volume
    save_config(config)

def save_mute_state(is_muted):
    config = load_config()
    config['is_muted'] = is_muted
    save_config(config)

def load_config():
    config_path = get_config_path()
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
            if not config or 'volume' not in config or 'is_muted' not in config:
                config = create_default_config()
                save_config(config)
        except json.JSONDecodeError:
            config = create_default_config()
            save_config(config)
    else:
        config = create_default_config()
        save_config(config)
    return config

def load_volume():
    config = load_config()
    return config['volume']

def initialize_volume():
    config = load_config()
    volume = config['volume']
    is_muted = config['is_muted']
    pygame.mixer.music.set_volume(volume)
    if is_muted:
        pygame.mixer.music.pause()
    else:
        pygame.mixer.music.unpause()

pygame.mixer.init()
pygame.mixer.music.load("assets/launchermusic.ogg")
is_muted = initialize_audio()
pygame.mixer.music.play(-1)
if is_muted:
    pygame.mixer.music.set_volume(0) 

def draw_credits_elements(canvas):
    canvas.delete("credits_elements")
    canvas.create_text(640, 50, text="CREDITS", font=("Faustina Regular", 26), fill="white", tags="credits_elements")
    
root = tk.Tk()
root.title("Launcher")
root.resizable(False, False)

container = tk.Frame(root)
container.pack(side="top", fill="both", expand=True)

container.grid_rowconfigure(0, weight=1)
container.grid_columnconfigure(1, weight=1)

settings_frame = tk.Frame(container)
launch_frame = tk.Frame(container)
credits_frame = tk.Frame(container)

for frame in (settings_frame, launch_frame, credits_frame):
    frame.grid(row=0, column=1, sticky="nsew")

launch_canvas = tk.Canvas(launch_frame, width=1280, height=720, bg='black', highlightthickness=0)
settings_canvas = tk.Canvas(settings_frame, width=1280, height=720, bg='black', highlightthickness=0)
credits_canvas = tk.Canvas(credits_frame, width=1280, height=720, bg='black', highlightthickness=0)

launch_canvas.grid(row=0, column=0, sticky="nsew")
settings_canvas.grid(row=0, column=0, sticky="nsew")
credits_canvas.grid(row=0, column=0, sticky="nsew")


def load_and_prepare_image(file_path):
    image = Image.open(file_path).convert("RGBA")
    return resize_image(image, 1280, 720)
    
def load_and_prepare_gif(file_path):
    image = Image.open(file_path)
    frames = []
    try:
        while True:
            frames.append(resize_image(image.copy(), 1280, 720))
            image.seek(image.tell() + 1)
    except EOFError:
        pass
    return frames

launch_image = load_and_prepare_image("assets/book.png")
settings_image = load_and_prepare_image("assets/book2.png")
credits_image = load_and_prepare_gif("assets/book3.png")

launch_photo = ImageTk.PhotoImage(launch_image)
settings_photo = ImageTk.PhotoImage(settings_image)
credits_photo = ImageTk.PhotoImage(credits_image[0])

launch_canvas.create_image(0, 0, image=launch_photo, anchor="nw")
settings_canvas.create_image(0, 0, image=settings_photo, anchor="nw")
credits_canvas.create_image(0, 0, image=credits_photo, anchor="nw")

draw_settings_elements()
draw_credits_elements(credits_canvas)

create_sidebar(launch_canvas, launch_image, launch_frame)
create_sidebar(settings_canvas, settings_image, settings_frame)
create_sidebar(credits_canvas, credits_image, credits_frame)

button_canvas = tk.Canvas(launch_frame, width=450, height=90, highlightthickness=0, bg=None)
button_canvas.place(relx=0.5, rely=1.0, anchor="s", y=-15)

button_bg_image = Image.open("assets/book.png")
button_bg_photo = ImageTk.PhotoImage(button_bg_image)
button_canvas.create_image(0, 0, image=button_bg_photo, anchor="nw")

def create_rounded_rectangle(canvas, x1, y1, x2, y2, radius, **kwargs):
    points = [x1+radius, y1, x2-radius, y1,
              x2, y1, x2, y1+radius,
              x2, y2-radius, x2, y2,
              x2-radius, y2, x1+radius, y2,
              x1, y2, x1, y2-radius,
              x1, y1+radius, x1, y1]
    return canvas.create_polygon(points, **kwargs, smooth=True)

button_bg = create_rounded_rectangle(button_canvas, 0, 0, 450, 90, 45, fill='#141414', outline='#dbc7a2', width=3)
button_text = button_canvas.create_text(225, 45, text="Launch", fill="#780606", font=("Faustina Regular", 32, "bold"))

def get_steam_install_path():
    try:
        reg_key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Wow6432Node\Valve\Steam")
        steam_path, _ = winreg.QueryValueEx(reg_key, "InstallPath")
        return steam_path
    except FileNotFoundError:
        raise FileNotFoundError("404")

def detect_tcoaal_game_install_path():
    try:
        steam_path = get_steam_install_path()
    except FileNotFoundError:
        raise FileNotFoundError("File not found.")

    library_file = os.path.join(steam_path, "steamapps", "libraryfolders.vdf")

    with open(library_file, 'r') as f:
        content = f.read()

    library_paths = re.findall(r'"path"\s+"([^"]+)"', content)

    library_paths.append(steam_path)

    for library_path in library_paths:
        game_path = os.path.join(library_path, "steamapps", "common")
        tcoaal_path = os.path.join(game_path, "The Coffin of Andy and Leyley")

        if os.path.exists(tcoaal_path):
            return tcoaal_path

base_directory = detect_tcoaal_game_install_path()
temp_dir = os.path.join(base_directory, "temp")
target_directory = os.path.join(base_directory, "final")
repo_zip_url = ""
print(base_directory)

def on_button_click(event):
    global is_processing, progress_fill, download_progress, is_download_complete
    if not is_processing:
        if not is_download_complete:
            is_processing = True
            if progress_fill is None:
                create_progress_bar(launch_canvas)
            threading.Thread(target=start_async_download).start()
            update_ui()
        else:
            is_processing = True
            is_download_complete = False
            download_progress = 0
            launch_canvas.coords(progress_fill, 417, 577, 417, 603)
            launch_canvas.itemconfig(progress_text, text="0%")
            threading.Thread(target=start_async_download).start()
            update_ui()

def update_ui():
    global is_processing, is_download_complete
    if progress_bar is not None:
        launch_canvas.itemconfig(progress_bar, state='normal')
        launch_canvas.itemconfig(progress_fill, state='normal')
        launch_canvas.itemconfig(progress_text, state='normal')
    update_progress_bar(launch_canvas, progress_fill, download_progress)
    if is_processing:
        root.after(100, update_ui)
    else:
        if is_download_complete:
            update_progress_bar(launch_canvas, progress_fill, 1.0)  
            root.after(5000, hide_progress_bar)

def reset_button():
    global button_text, is_processing, is_download_complete
    button_canvas.delete("all")
    button_canvas.create_image(0, 0, image=button_bg_photo, anchor="nw")
    button_bg = create_rounded_rectangle(button_canvas, 0, 0, 450, 90, 45, fill='#141414', outline='#dbc7a2', width=3)
    button_text = button_canvas.create_text(225, 45, text="Launch", fill="#780606", font=("Faustina Regular", 32, "bold"))
    is_processing = False
    is_download_complete = False

button_canvas.bind("<Button-1>", on_button_click)
button_canvas.bind("<Enter>", lambda e: button_canvas.config(cursor="hand2"))
button_canvas.bind("<Leave>", lambda e: button_canvas.config(cursor=""))

current_canvas = launch_canvas
current_image = launch_image

show_frame(launch_frame)
progress_fill = create_progress_bar(launch_canvas)

icon = tk.PhotoImage(file = 'assets\icon.png')
root.wm_iconphoto(False, icon)
root.mainloop()
