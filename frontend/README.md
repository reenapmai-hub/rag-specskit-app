# RAG Document Search - Frontend

A modern, responsive web UI for uploading documents and semantic search powered by Gemini embeddings and ChromaDB Cloud.

## Features

- 📄 **File Upload**: Drag & drop or click to upload .txt, .md, and .pdf files
- 🔍 **Semantic Search**: Query documents with natural language questions
- ✨ **Progress Tracking**: Visual feedback with "Embedding via Gemini..." progress bar
- 📊 **Results Display**: Shows chunk text, similarity scores, source files, and chunk positions
- 📈 **Collection Stats**: Displays total chunks in collection and last sync time
- 🔄 **Reset Collection**: Clear all documents with confirmation modal
- 🎨 **Responsive UI**: Beautiful gradient design that works on all screen sizes

## Quick Start

### Option 1: Python HTTP Server (Recommended)

```bash
cd frontend
python -m http.server 3000
```

Then open: `http://localhost:3000`

### Option 2: Direct File Open

Simply open `frontend/index.html` in your browser (limited functionality for uploads).

## Configuration

The frontend connects to the backend API at `http://localhost:5001/api`.

To use a different API host, set before loading:

```javascript
window.API_BASE = "http://your-server:5001/api";
```

Or in a script tag in HTML:

```html
<script>
  window.API_BASE = "http://your-server:5001/api";
</script>
```

## API Endpoints Used

- `POST /api/upload` - Upload and process documents
- `POST /api/query` - Search similar documents
- `DELETE /api/reset` - Reset collection
- `GET /healthz` - Health check

## Requirements

- Backend API running on port 5001
- Modern web browser (Chrome, Firefox, Safari, Edge)
- JavaScript enabled

## File Size Limits

- Individual files: <100MB recommended
- PDF files: ~50MB for optimal performance
