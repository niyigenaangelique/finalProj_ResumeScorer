from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from database import ResumeDatabase
from hr_base import get_current_user
import os
import mimetypes

# Initialize database
db = ResumeDatabase()

def get_pdf_viewer_page(document_id: int, document_info: dict) -> str:
    """Generate a proper PDF viewer page"""
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>PDF Viewer - {document_info.get('filename', 'Document')}</title>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.min.js"></script>
        <style>
            body {{
                font-family: Arial, sans-serif;
                margin: 0;
                padding: 0;
                background: #f5f5f5;
            }}
            .header {{
                background: #2c3e50;
                color: white;
                padding: 15px 20px;
                display: flex;
                justify-content: space-between;
                align-items: center;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }}
            .header h2 {{
                margin: 0;
                font-size: 18px;
            }}
            .file-info {{
                font-size: 14px;
                opacity: 0.9;
            }}
            .close-btn {{
                background: #e74c3c;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                cursor: pointer;
                text-decoration: none;
            }}
            .close-btn:hover {{
                background: #c0392b;
            }}
            .pdf-container {{
                height: calc(100vh - 70px);
                display: flex;
                flex-direction: column;
            }}
            .toolbar {{
                background: white;
                padding: 10px;
                border-bottom: 1px solid #ddd;
                display: flex;
                align-items: center;
                gap: 10px;
                box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            }}
            .toolbar button {{
                background: #3498db;
                color: white;
                border: none;
                padding: 6px 12px;
                border-radius: 4px;
                cursor: pointer;
                font-size: 12px;
            }}
            .toolbar button:hover {{
                background: #2980b9;
            }}
            .toolbar button:disabled {{
                background: #bdc3c7;
                cursor: not-allowed;
            }}
            .page-info {{
                margin: 0 10px;
                font-size: 14px;
                color: #555;
            }}
            #pdf-canvas {{
                flex: 1;
                background: white;
                margin: 20px auto;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                display: block;
            }}
            .loading {{
                display: flex;
                justify-content: center;
                align-items: center;
                height: 400px;
                font-size: 18px;
                color: #666;
            }}
            .error {{
                display: flex;
                justify-content: center;
                align-items: center;
                height: 400px;
                flex-direction: column;
                color: #e74c3c;
            }}
            .zoom-controls {{
                display: flex;
                align-items: center;
                gap: 5px;
            }}
            .zoom-controls input[type="range"] {{
                width: 100px;
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <div>
                <h2>PDF Document Viewer</h2>
                <div class="file-info">
                    {document_info.get('filename', 'Unknown')} 
                    ({round(document_info.get('file_size', 0) / 1024, 2)} KB)
                </div>
            </div>
            <a href="javascript:window.close()" class="close-btn">Close</a>
        </div>
        
        <div class="pdf-container">
            <div class="toolbar">
                <button id="prev-page" onclick="previousPage()">Previous</button>
                <button id="next-page" onclick="nextPage()">Next</button>
                <div class="page-info">
                    Page: <span id="page-num">0</span> / <span id="page-count">0</span>
                </div>
                
                <div class="zoom-controls">
                    <button onclick="zoomOut()">−</button>
                    <input type="range" id="zoom-slider" min="50" max="200" value="100" onchange="setZoom(this.value)">
                    <button onclick="zoomIn()">+</button>
                    <span id="zoom-level">100%</span>
                </div>
                
                <button onclick="rotateLeft()">↺ Rotate Left</button>
                <button onclick="rotateRight()">↻ Rotate Right</button>
                <button onclick="downloadPDF()">⬇ Download</button>
            </div>
            
            <div id="loading" class="loading">
                Loading PDF document...
            </div>
            
            <div id="error" class="error" style="display: none;">
                <h3>Unable to load PDF</h3>
                <p>The PDF file could not be loaded. This might be because:</p>
                <ul style="text-align: left; max-width: 400px;">
                    <li>The file doesn't exist on the server</li>
                    <li>The file is not a valid PDF</li>
                    <li>The file is corrupted</li>
                </ul>
                <button onclick="downloadPDF()">Download File Instead</button>
            </div>
            
            <canvas id="pdf-canvas" style="display: none;"></canvas>
        </div>

        <script>
            let pdfDoc = null;
            let pageNum = 1;
            let pageRendering = false;
            let pageNumPending = null;
            let scale = 1.0;
            let rotation = 0;
            
            // Load the PDF document
            function loadPDF() {{
                const url = '/api/pdf-file/{document_id}';
                
                pdfjsLib.getDocument(url).promise.then(function(pdf) {{
                    pdfDoc = pdf;
                    document.getElementById('page-count').textContent = pdf.numPages;
                    document.getElementById('loading').style.display = 'none';
                    document.getElementById('pdf-canvas').style.display = 'block';
                    
                    // Initial render
                    renderPage(pageNum);
                }}).catch(function(error) {{
                    console.error('Error loading PDF:', error);
                    document.getElementById('loading').style.display = 'none';
                    document.getElementById('error').style.display = 'flex';
                }});
            }}
            
            // Render page
            function renderPage(num) {{
                pageRendering = true;
                
                pdfDoc.getPage(num).then(function(page) {{
                    const viewport = page.getViewport({{ scale: scale, rotation: rotation }});
                    const canvas = document.getElementById('pdf-canvas');
                    const context = canvas.getContext('2d');
                    canvas.height = viewport.height;
                    canvas.width = viewport.width;
                    
                    const renderContext = {{
                        canvasContext: context,
                        viewport: viewport
                    }};
                    
                    const renderTask = page.render(renderContext);
                    
                    renderTask.promise.then(function() {{
                        pageRendering = false;
                        if (pageNumPending !== null) {{
                            renderPage(pageNumPending);
                            pageNumPending = null;
                        }}
                    }});
                }});
                
                document.getElementById('page-num').textContent = num;
            }}
            
            // Queue render page
            function queueRenderPage(num) {{
                if (pageRendering) {{
                    pageNumPending = num;
                }} else {{
                    renderPage(num);
                }}
            }}
            
            // Previous page
            function previousPage() {{
                if (pageNum <= 1) {{
                    return;
                }}
                pageNum--;
                queueRenderPage(pageNum);
            }}
            
            // Next page
            function nextPage() {{
                if (pageNum >= pdfDoc.numPages) {{
                    return;
                }}
                pageNum++;
                queueRenderPage(pageNum);
            }}
            
            // Zoom functions
            function setZoom(value) {{
                scale = value / 100;
                document.getElementById('zoom-level').textContent = value + '%';
                queueRenderPage(pageNum);
            }}
            
            function zoomIn() {{
                const slider = document.getElementById('zoom-slider');
                const newValue = Math.min(parseInt(slider.value) + 10, 200);
                slider.value = newValue;
                setZoom(newValue);
            }}
            
            function zoomOut() {{
                const slider = document.getElementById('zoom-slider');
                const newValue = Math.max(parseInt(slider.value) - 10, 50);
                slider.value = newValue;
                setZoom(newValue);
            }}
            
            // Rotation functions
            function rotateLeft() {{
                rotation = (rotation - 90) % 360;
                queueRenderPage(pageNum);
            }}
            
            function rotateRight() {{
                rotation = (rotation + 90) % 360;
                queueRenderPage(pageNum);
            }}
            
            // Download PDF
            function downloadPDF() {{
                window.open('/download-document/{document_id}', '_blank');
            }}
            
            // Keyboard shortcuts
            document.addEventListener('keydown', function(e) {{
                if (e.key === 'ArrowLeft') {{
                    previousPage();
                }} else if (e.key === 'ArrowRight') {{
                    nextPage();
                }} else if (e.key === '+' || e.key === '=') {{
                    zoomIn();
                }} else if (e.key === '-' || e.key === '_') {{
                    zoomOut();
                }}
            }});
            
            // Load PDF when page loads
            loadPDF();
        </script>
    </body>
    </html>
    """
