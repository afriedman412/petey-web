/**
 * Shared dropzone component for PDF file selection.
 *
 * Usage: <drop-zone max-files="5000"></drop-zone>
 *
 * Events:
 *   - 'files-selected': detail = { files: File[] }
 *
 * Methods:
 *   - setEnabled(bool) — enable/disable file selection
 *   - setGateMessage(html) — show a message instead of the drop prompt (e.g. "set API key")
 *   - clearGate() — restore normal drop prompt
 *   - reset() — clear selected files and restore default state
 *   - getFiles() — returns current File[]
 */

const DROPZONE_STYLE_ID = 'dropzone-shared-css';
if (!document.getElementById(DROPZONE_STYLE_ID)) {
  const style = document.createElement('style');
  style.id = DROPZONE_STYLE_ID;
  style.textContent = `
    .dropzone {
      border: 1.5px dashed var(--border, #333); border-radius: var(--r-lg, 12px);
      padding: 2.75rem 2rem; text-align: center; cursor: pointer;
      background: var(--surface, #1c1c1c); margin-bottom: 1.5rem;
      background-image: radial-gradient(circle, var(--border, #333) 1px, transparent 1px);
      background-size: 22px 22px; background-position: center;
      transition: border-color 0.2s, background-color 0.2s;
    }
    .dropzone:hover, .dropzone.over {
      border-color: var(--accent, #d8572a); background-color: var(--accent-dim, rgba(216,87,42,0.12));
    }
    .dropzone.has-file {
      border-color: var(--green, #86efac); border-style: solid;
      background-color: rgba(52,211,153,0.05); background-image: none;
    }
    .dropzone p { font-size: 0.88rem; color: var(--text-muted, #db7c26); }
    .dropzone.has-file p { color: var(--green, #86efac); font-weight: 500; }
    .dropzone input { display: none; }
    .dropzone.gated { opacity: 0.6; cursor: default; }
    .dropzone.gated:hover { border-color: var(--border, #333); background-color: var(--surface, #1c1c1c); }
  `;
  document.head.appendChild(style);
}

class DropZone extends HTMLElement {
  constructor() {
    super();
    this._files = [];
    this._enabled = true;
    this._gated = false;
    this._maxFiles = 5000;
  }

  connectedCallback() {
    this._maxFiles = parseInt(this.getAttribute('max-files') || '5000', 10);

    this.innerHTML = `
      <div class="dropzone" id="dropzone">
        <p id="dropLabel">Drop PDFs here, or click to select</p>
        <input type="file" id="fileInput" accept=".pdf" multiple>
      </div>
    `;

    this._dz = this.querySelector('.dropzone');
    this._label = this.querySelector('#dropLabel');
    this._input = this.querySelector('input');

    this._dz.addEventListener('click', () => {
      if (this._enabled && !this._gated) this._input.click();
    });

    this._dz.addEventListener('dragover', e => {
      e.preventDefault();
      if (this._enabled && !this._gated) this._dz.classList.add('over');
    });

    this._dz.addEventListener('dragleave', () => this._dz.classList.remove('over'));

    this._dz.addEventListener('drop', e => {
      e.preventDefault();
      this._dz.classList.remove('over');
      if (!this._enabled || this._gated) return;
      const pdfs = [...e.dataTransfer.files].filter(f => f.name.toLowerCase().endsWith('.pdf'));
      if (pdfs.length) this._setFiles(pdfs);
    });

    this._input.addEventListener('change', e => {
      const pdfs = [...e.target.files].filter(f => f.name.toLowerCase().endsWith('.pdf'));
      if (pdfs.length) this._setFiles(pdfs);
    });
  }

  _setFiles(files) {
    if (files.length > this._maxFiles) {
      files = files.slice(0, this._maxFiles);
      alert('Maximum ' + this._maxFiles + ' documents at a time. Only the first ' + this._maxFiles + ' will be used.');
    }
    this._files = files;
    this._label.textContent = files.length === 1 ? files[0].name : files.length + ' PDFs selected';
    this._dz.classList.add('has-file');
    this.dispatchEvent(new CustomEvent('files-selected', { detail: { files } }));
  }

  setEnabled(enabled) {
    this._enabled = enabled;
    if (this._input) this._input.disabled = !enabled;
  }

  setGateMessage(html) {
    this._gated = true;
    this._dz.classList.add('gated');
    this._label.innerHTML = html;
    this._input.disabled = true;
  }

  clearGate() {
    this._gated = false;
    this._dz.classList.remove('gated');
    this._label.textContent = 'Drop PDFs here, or click to select';
    this._input.disabled = false;
  }

  reset() {
    this._files = [];
    this._dz.classList.remove('has-file');
    this._input.value = '';
    if (!this._gated) {
      this._label.textContent = 'Drop PDFs here, or click to select';
    }
  }

  getFiles() {
    return this._files;
  }
}

customElements.define('drop-zone', DropZone);
