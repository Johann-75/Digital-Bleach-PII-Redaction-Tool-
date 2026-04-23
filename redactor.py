import fitz
import re
import json
import os

try:
    import nltk
    from nltk import word_tokenize, pos_tag, ne_chunk
    NLTK_AVAILABLE = True
except ImportError:
    NLTK_AVAILABLE = False


class Redactor:
    def __init__(self, pdf_stream, config_path="rules.json"):
        self.doc = fitz.open(stream=pdf_stream, filetype="pdf")
        self.config = self._load_config(config_path)
        self._compile_patterns()

    def _load_config(self, path):
        """Loads the configuration from a JSON file."""
        if not os.path.exists(path):
            # Fallback to absolute path relative to this file if not found
            base_path = os.path.dirname(os.path.abspath(__file__))
            path = os.path.join(base_path, path)
            
        with open(path, 'r') as f:
            return json.load(f)

    def _compile_patterns(self):
        """Pre-compiles all regex patterns for high-speed processing."""
        # 1. PII Patterns (Direct sweep)
        self.pii_res = [re.compile(pattern) for pattern in self.config['pii_patterns'].values()]
        
        # 2. Labeled Line Pattern
        labels_joined = "|".join(self.config['label_keywords'])
        self.labeled_line_re = re.compile(
            rf'(?i)(?:[\w\s]+?)(?:{labels_joined})(?:[\w\s]*?)\s*[:\-]\s*(.+)'
        )
        
        # 3. Prose Name Pattern
        roles_joined = "|".join(self.config['prose_role_keywords'])
        self.prose_name_re = re.compile(
            rf'(?i)(?:{roles_joined})\s*,?\s+([A-Z][a-z]+(?: [A-Z][a-z]+)+)'
        )
        
        # 4. Stop-words for filtering
        self.non_pii_words = set(self.config['non_pii_labels'])

    @staticmethod
    def setup_nltk():
        if not NLTK_AVAILABLE:
            return
        resources = [
            'punkt', 'punkt_tab', 'averaged_perceptron_tagger',
            'averaged_perceptron_tagger_eng', 'maxent_ne_chunker',
            'maxent_ne_chunker_tab', 'words',
        ]
        for res in resources:
            try:
                nltk.data.find(f'tokenizers/{res}') if 'punkt' in res else \
                nltk.data.find(f'taggers/{res}') if 'tagger' in res else \
                nltk.data.find(f'chunkers/{res}') if 'chunker' in res else \
                nltk.data.find(f'corpora/{res}')
            except (LookupError, Exception):
                try:
                    nltk.download(res, quiet=True)
                except Exception:
                    pass

    def get_confidential_entities(self, text):
        entities = set()

        # ── Layer 1: Regex on labeled lines ─────────────────────────────────
        for line in text.splitlines():
            m = self.labeled_line_re.match(line.strip())
            if m:
                val = m.group(1).strip()
                for pii_re in self.pii_res:
                    matches = pii_re.findall(val)
                    for m_val in matches:
                        if isinstance(m_val, tuple):
                            entities.update([x for x in m_val if x])
                        else:
                            entities.add(m_val)

        # Full-text sweep for PII values
        for pii_re in self.pii_res:
            matches = pii_re.findall(text)
            for m_val in matches:
                if isinstance(m_val, tuple):
                    entities.update([x for x in m_val if x])
                else:
                    entities.add(m_val)

        # ── Layer 2: Prose name extraction ───────────────────────────────────
        for match in self.prose_name_re.finditer(text):
            name = match.group(1).strip(".,;: ")
            if not any(w in self.non_pii_words for w in name.lower().split()):
                entities.add(name)

        # ── Layer 3: NLTK NER (Fast Fallback) ────────────────────────────────
        if NLTK_AVAILABLE:
            try:
                chunks = ne_chunk(pos_tag(word_tokenize(text)))
                for chunk in chunks:
                    if hasattr(chunk, 'label') and chunk.label() == 'PERSON':
                        name = " ".join(c[0] for c in chunk.leaves()).strip(".,;:()")
                        if any(w in self.non_pii_words for w in name.lower().split()):
                            continue
                        if name.isupper():
                            continue
                        if name.istitle() and len(name) > 2:
                            entities.add(name)
            except Exception:
                pass

        return sorted([e for e in entities if e.strip()], key=len, reverse=True)

    def redact_page(self, page_index):
        page = self.doc[page_index]
        text = page.get_text("text")
        if not text.strip():
            return False
        for item in self.get_confidential_entities(text):
            for rect in page.search_for(item):
                page.add_redact_annot(rect, fill=(0, 0, 0))
        page.apply_redactions()
        return True

    def redact_all(self):
        for i in range(len(self.doc)):
            self.redact_page(i)
        return self.doc

    def save(self):
        return self.doc.tobytes()

    def get_page_image(self, page_index):
        page = self.doc[page_index]
        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
        return pix.tobytes()