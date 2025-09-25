import streamlit as st
import heapq
import os
import pickle
import base64
import time
from datetime import datetime
import mimetypes
from pathlib import Path

# --------------------------
# Huffman Coding
# --------------------------

class Node:
    def __init__(self, char, freq):
        self.char = char
        self.freq = freq
        self.left = None
        self.right = None

    # Comparison for heap
    def __lt__(self, other):
        return self.freq < other.freq


def build_frequency_table(data: str):
    freq = {}
    for ch in data:
        freq[ch] = freq.get(ch, 0) + 1
    return freq


def build_huffman_tree(freq):
    heap = [Node(ch, f) for ch, f in freq.items()]
    heapq.heapify(heap)

    while len(heap) > 1:
        left = heapq.heappop(heap)
        right = heapq.heappop(heap)
        merged = Node(None, left.freq + right.freq)
        merged.left = left
        merged.right = right
        heapq.heappush(heap, merged)

    return heap[0] if heap else None


def build_codes(node, prefix="", code_map={}):
    if not node:
        return

    if node.char is not None:
        code_map[node.char] = prefix
        return

    build_codes(node.left, prefix + "0", code_map)
    build_codes(node.right, prefix + "1", code_map)


def huffman_compress(text: str):
    if not text:
        raise ValueError("Empty input cannot be compressed.")

    freq = build_frequency_table(text)
    root = build_huffman_tree(freq)

    codes = {}
    build_codes(root, "", codes)

    encoded_text = "".join(codes[ch] for ch in text)

    # pad encoded text to byte alignment
    padding = 8 - len(encoded_text) % 8
    encoded_text += "0" * padding

    padded_info = "{0:08b}".format(padding)
    encoded_text = padded_info + encoded_text

    # convert to bytes
    b = bytearray()
    for i in range(0, len(encoded_text), 8):
        byte = encoded_text[i:i + 8]
        b.append(int(byte, 2))

    # Store with pickle: compressed data + codes
    return pickle.dumps((bytes(b), codes))


def huffman_decompress(data: bytes):
    try:
        b, codes = pickle.loads(data)
    except Exception as e:
        raise ValueError("Corrupted compressed file.")

    # reverse map
    rev_codes = {v: k for k, v in codes.items()}

    bit_string = ""
    for byte in b:
        bit_string += "{0:08b}".format(byte)

    # remove padding
    padding = int(bit_string[:8], 2)
    bit_string = bit_string[8:]
    bit_string = bit_string[:-padding] if padding > 0 else bit_string

    decoded_text = ""
    code = ""
    for bit in bit_string:
        code += bit
        if code in rev_codes:
            decoded_text += rev_codes[code]
            code = ""

    if code != "":
        raise ValueError("Incomplete prefix code in compressed file.")

    return decoded_text


# --------------------------
# Helper Functions
# --------------------------

def get_file_icon(file_name):
    """Get appropriate icon based on file extension"""
    ext = Path(file_name).suffix.lower()
    icons = {
        '.txt': '📄', '.huff': '🗜️', '.py': '🐍', '.js': '📜', 
        '.html': '🌐', '.css': '🎨', '.json': '📋', '.xml': '📄',
        '.md': '📝', '.csv': '📊', '.log': '📋'
    }
    return icons.get(ext, '📁')

def format_file_size(size_bytes):
    """Format file size in human readable format"""
    if size_bytes == 0:
        return "0 B"
    size_names = ["B", "KB", "MB", "GB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    return f"{size_bytes:.1f} {size_names[i]}"

def calculate_compression_ratio(original_size, compressed_size):
    """Calculate compression ratio percentage"""
    if original_size == 0:
        return 0
    return ((original_size - compressed_size) / original_size) * 100

def get_file_type_description(file_name):
    """Get human readable file type description"""
    ext = Path(file_name).suffix.lower()
    types = {
        '.txt': 'Text Document', '.py': 'Python Script', '.js': 'JavaScript',
        '.html': 'HTML Document', '.css': 'Stylesheet', '.json': 'JSON Data',
        '.xml': 'XML Document', '.md': 'Markdown', '.csv': 'CSV Data',
        '.huff': 'Huffman Compressed File'
    }
    return types.get(ext, 'Unknown File Type')

# --------------------------
# Streamlit App
# --------------------------

st.set_page_config(
    page_title="Premium Huffman File Compressor",
    page_icon="🗜️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for premium styling
st.markdown("""
<style>
    /* Import Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    /* Main app styling */
    .main .block-container {
        padding-top: 0.5rem;
        padding-bottom: 0.5rem;
        max-width: 1200px;
        height: 100vh;
        overflow: hidden !important;
    }
    
    /* Prevent all scrolling */
    .main {
        overflow: hidden !important;
        height: 100vh !important;
    }
    
    /* Force no scroll on body */
    body {
        overflow: hidden !important;
    }
    
    /* Header styling */
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 0.5rem;
        text-align: center;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
    
    .main-header h1 {
        color: white !important;
        font-family: 'Inter', sans-serif;
        font-weight: 700;
        font-size: 1.8rem;
        margin: 0;
        text-shadow: 0 2px 4px rgba(0,0,0,0.3);
    }
    
    .main-header p {
        color: rgba(255,255,255,0.9) !important;
        font-size: 0.9rem;
        margin: 0.2rem 0 0 0;
        font-weight: 400;
    }
    
    /* Card styling */
    .premium-card {
        background: white;
        padding: 1rem;
        border-radius: 10px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        margin-bottom: 0.5rem;
        border: 1px solid rgba(255,255,255,0.2);
    }
    
    .stats-card {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        text-align: center;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
    
    .stats-number {
        font-size: 2.5rem;
        font-weight: 700;
        margin: 0;
    }
    
    .stats-label {
        font-size: 0.9rem;
        opacity: 0.9;
        margin: 0;
    }
    
    /* File upload area */
    .stFileUploader > div > div {
        border: 2px dashed #667eea !important;
        border-radius: 15px !important;
        background: linear-gradient(135deg, #f8f9ff 0%, #e8ecff 100%) !important;
    }
    
    /* Button styling */
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 10px !important;
        padding: 0.75rem 2rem !important;
        font-weight: 600 !important;
        font-size: 1.1rem !important;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4) !important;
        transition: all 0.3s ease !important;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 25px rgba(102, 126, 234, 0.6) !important;
    }
    
    /* Download button */
    .download-btn {
        background: linear-gradient(135deg, #56ab2f 0%, #a8e6cf 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 10px !important;
        padding: 0.75rem 2rem !important;
        font-weight: 600 !important;
        box-shadow: 0 4px 15px rgba(86, 171, 47, 0.4) !important;
    }
    
    /* Radio button styling */
    .stRadio > div {
        background: white;
        padding: 1rem;
        border-radius: 10px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
    
    /* Success/Error message styling */
    .stSuccess {
        background: linear-gradient(135deg, #56ab2f 0%, #a8e6cf 100%) !important;
        color: white !important;
        border-radius: 10px !important;
        padding: 1rem !important;
    }
    
    .stError {
        background: linear-gradient(135deg, #ff416c 0%, #ff4b2b 100%) !important;
        color: white !important;
        border-radius: 10px !important;
        padding: 1rem !important;
    }
    
    .stWarning {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%) !important;
        color: white !important;
        border-radius: 10px !important;
        padding: 1rem !important;
    }
    
    /* Progress bar */
    .stProgress > div > div > div > div {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
    }
    
    /* Sidebar styling */
    .css-1d391kg {
        background: linear-gradient(180deg, #667eea 0%, #764ba2 100%) !important;
    }
    
    /* File info display */
    .file-info {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
        text-align: center;
    }
    
    .file-icon {
        font-size: 2rem;
        margin-bottom: 0.3rem;
    }
    
    .file-name {
        font-size: 1.1rem;
        font-weight: 600;
        margin: 0.3rem 0;
    }
    
    .file-details {
        font-size: 0.8rem;
        opacity: 0.9;
        margin: 0.1rem 0;
    }
    
    /* Hide streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Remove all default spacing and margins */
    .stApp > div {
        padding: 0 !important;
        margin: 0 !important;
    }
    
    /* Compact spacing for all elements */
    .stMarkdown, .stFileUploader, .stRadio, .stButton {
        margin-bottom: 0.5rem !important;
    }
    
    /* Ensure no overflow on any container */
    * {
        box-sizing: border-box;
    }
</style>
""", unsafe_allow_html=True)

# Main header
st.markdown("""
<div class="main-header">
    <h1>🗜️ Premium Huffman Compressor</h1>
    <p>Advanced file compression with intelligent algorithms and beautiful interface</p>
</div>
""", unsafe_allow_html=True)

# Sidebar for additional features
with st.sidebar:
    st.markdown("## 🛠️ Tools & Settings")
    
    # Compression level (for future enhancement)
    compression_level = st.selectbox(
        "Compression Level",
        ["Standard", "High", "Maximum"],
        index=0
    )
    
    # File type filters
    file_types = st.multiselect(
        "Supported File Types",
        ["Text (.txt)", "Python (.py)", "JavaScript (.js)", "HTML (.html)", "CSS (.css)", "JSON (.json)", "Markdown (.md)", "All Files"],
        default=["All Files"]
    )
    
    st.markdown("---")
    
    # Statistics
    st.markdown("## 📊 Compression Stats")
    if 'total_compressed' not in st.session_state:
        st.session_state.total_compressed = 0
    if 'total_saved' not in st.session_state:
        st.session_state.total_saved = 0
    
    st.metric("Files Compressed", st.session_state.total_compressed)
    st.metric("Space Saved", f"{st.session_state.total_saved:.1f} KB")

# Main content area
col1, col2 = st.columns([2, 1])

with col1:
    st.markdown('<div class="premium-card">', unsafe_allow_html=True)
    
    # File upload section
    st.markdown("### 📁 Upload Your File")
    uploaded_file = st.file_uploader(
        "Choose a file to compress or decompress",
        type=None,
        help="Upload any text file for compression or .huff file for decompression"
    )
    
    # Operation mode
    st.markdown("### ⚙️ Operation Mode")
    mode = st.radio(
        "Choose what you want to do:",
        ["🗜️ Compress File", "📤 Decompress File"],
        horizontal=True,
        label_visibility="collapsed"
    )
    
    st.markdown('</div>', unsafe_allow_html=True)

with col2:
    st.markdown('<div class="stats-card">', unsafe_allow_html=True)
    st.markdown("### 📈 Quick Stats")
    st.markdown(f"**Compression Level:** {compression_level}")
    st.markdown(f"**Supported Types:** {len(file_types)}")
    st.markdown(f"**Session Time:** {datetime.now().strftime('%H:%M:%S')}")
    st.markdown('</div>', unsafe_allow_html=True)

# File processing section
if uploaded_file:
    # File information display
    file_icon = get_file_icon(uploaded_file.name)
    file_size = format_file_size(uploaded_file.size)
    file_type = get_file_type_description(uploaded_file.name)
    
    st.markdown(f"""
    <div class="file-info">
        <div class="file-icon">{file_icon}</div>
        <div class="file-name">{uploaded_file.name}</div>
        <div class="file-details">Size: {file_size}</div>
        <div class="file-details">Type: {file_type}</div>
        <div class="file-details">Uploaded: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Process button
    if st.button("🚀 Process File", use_container_width=True):
        # Create progress bar
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        try:
            input_bytes = uploaded_file.read()

            if len(input_bytes) == 0:
                st.error("❌ The uploaded file is empty!")
            else:
                # Update progress
                progress_bar.progress(25)
                status_text.text("📖 Reading file...")
                time.sleep(0.5)
                
                if "Compress" in mode:
                    progress_bar.progress(50)
                    status_text.text("🗜️ Compressing with Huffman algorithm...")
                    
                    try:
                        text = input_bytes.decode("utf-8")
                    except Exception:
                        st.error("❌ Only UTF-8 text files are supported for compression.")
                        text = None

                    if text:
                        compressed = huffman_compress(text)
                        compressed_size = len(compressed)
                        original_size = len(input_bytes)
                        compression_ratio = calculate_compression_ratio(original_size, compressed_size)
                        
                        progress_bar.progress(100)
                        status_text.text("✅ Compression completed!")
                        time.sleep(0.5)
                        
                        # Update session stats
                        st.session_state.total_compressed += 1
                        st.session_state.total_saved += (original_size - compressed_size) / 1024
                        
                        # Success message with stats
                        st.success(f"🎉 **Compression Successful!**")
                        
                        # Display compression statistics
                        col1, col2, col3, col4 = st.columns(4)
                        with col1:
                            st.metric("Original Size", format_file_size(original_size))
                        with col2:
                            st.metric("Compressed Size", format_file_size(compressed_size))
                        with col3:
                            st.metric("Compression Ratio", f"{compression_ratio:.1f}%")
                        with col4:
                            st.metric("Space Saved", format_file_size(original_size - compressed_size))
                        
                        # Download button
                        out_name = uploaded_file.name + ".huff"
                        st.download_button(
                            label="💾 Download Compressed File",
                            data=compressed,
                            file_name=out_name,
                            mime="application/octet-stream",
                            use_container_width=True
                        )
                        
                        # Clear progress
                        progress_bar.empty()
                        status_text.empty()

                else:  # Decompress
                    progress_bar.progress(50)
                    status_text.text("📤 Decompressing file...")
                    
                    try:
                        decompressed = huffman_decompress(input_bytes)
                        decompressed_size = len(decompressed.encode('utf-8'))
                        original_size = len(input_bytes)
                        
                        progress_bar.progress(100)
                        status_text.text("✅ Decompression completed!")
                        time.sleep(0.5)
                        
                        # Success message
                        st.success(f"🎉 **Decompression Successful!**")
                        
                        # Display decompression statistics
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Compressed Size", format_file_size(original_size))
                        with col2:
                            st.metric("Decompressed Size", format_file_size(decompressed_size))
                        with col3:
                            expansion_ratio = ((decompressed_size - original_size) / original_size) * 100
                            st.metric("Expansion Ratio", f"{expansion_ratio:.1f}%")
                        
                        # Download button
                        out_name = uploaded_file.name.replace(".huff", "_decompressed.txt")
                        st.download_button(
                            label="💾 Download Decompressed File",
                            data=decompressed.encode("utf-8"),
                            file_name=out_name,
                            mime="text/plain",
                            use_container_width=True
                        )
                        
                        # Clear progress
                        progress_bar.empty()
                        status_text.empty()
                        
                    except Exception as e:
                        progress_bar.empty()
                        status_text.empty()
                        st.error(f"❌ **Decompression Failed:** {str(e)}")

        except Exception as e:
            progress_bar.empty()
            status_text.empty()
            st.error(f"⚠️ **Unexpected Error:** {str(e)}")



