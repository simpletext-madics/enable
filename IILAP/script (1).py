import gradio as gr
import subprocess
import re
import sys

def launch_app_b():
    """
    Launch App B as a subprocess and capture its public URL.
    """
    proc = subprocess.Popen(
        [sys.executable, "-u", "/content/drive/MyDrive/IILAP CODE/student_interface.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        bufsize=1  # Line-buffered
    )

    public_url = None
    while True:
        line = proc.stdout.readline()
        if not line:
            break
        decoded_line = line.decode("utf-8").strip()
        print(decoded_line)  # Debugging output
        
        match = re.search(r'(https?://\S*gradio\.live\S*)', decoded_line)
        if match:
            public_url = match.group(1)
            break  # Stop once the public URL is found

    return f'<a href="{public_url}" target="_blank" style="font-size:16px; font-weight:bold; color:#007bff;">Click to continue</a>' if public_url else "Failed to capture App B URL."

def generate_app_b(agree):
    """
    Called when user clicks 'Generate My Access Link'. Only works if they agreed to T&C.
    """
    if not agree:
        return '<span style="color:red; font-weight:bold;">❌ You must accept the Terms and Conditions to proceed.</span>'
    return launch_app_b()

# Gradio Interface
with gr.Blocks(css=".small-button {width: 200px; height: 45px;}") as iface:
    gr.Markdown("## 🎓 Research Participation Portal ")
    gr.Markdown("**Press 'Generate My Access Link' to receive your personal link.**")

    # Terms and Conditions section
    gr.Markdown(
        '📜 By participating, you agree to our <a href="https://drive.google.com/file/d/1Ccp_JGhuDUOyR99w3VgrGlN2H5dkmrbo/view?usp=sharing" target="_blank">Terms and Conditions</a>.'
        '<br>Please read them carefully before proceeding.', 
        elem_id="terms", 
    )

    agree = gr.Checkbox(label="I have read and accept the Terms and Conditions", value=False)
    
    with gr.Row():
        generate_button = gr.Button("Generate My Access Link", elem_classes=["small-button"], interactive=False)
        gr.Markdown("_(This could take a couple of seconds...)_", elem_id="loading-text")

    output = gr.HTML()

    agree.change(lambda x: gr.update(interactive=x), inputs=agree, outputs=generate_button)
    generate_button.click(generate_app_b, inputs=[agree], outputs=output)

iface.launch(share=True, inbrowser=False)

demo = gr.Interface(fn=lambda x: x, inputs="text", outputs="text")
demo.launch(share=True, inbrowser=False)
