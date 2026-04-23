# 🔐 Digital Bleach: Enterprise PII Redaction Engine

[cite_start]**Digital Bleach** is a localized, zero-trust document security tool designed to automatically scrub sensitive Personally Identifiable Information (PII) from PDF documents[cite: 27, 28]. [cite_start]It utilizes a multi-layered hybrid NLP architecture to ensure high precision while maintaining document context and structural integrity[cite: 20, 22].

---

## 🚀 Core Architecture: The 3-Layer Logic

[cite_start]The system employs three distinct detection layers to balance speed with semantic accuracy[cite: 22]:

1.  [cite_start]**Layer 1 (Labeled Lines)**: Uses deterministic regex to isolate values following specific descriptors (e.g., "Phone:", "PAN:")[cite: 22, 54, 55]. [cite_start]This prevents "label bleed" by masking only the sensitive value while keeping the descriptor visible[cite: 21, 27].
2.  [cite_start]**Layer 2 (Prose Extraction)**: Utilizes role-based keyword patterns (e.g., "Owner", "Tenant", "Employee") to detect and mask names embedded within natural language paragraphs[cite: 22, 41, 45].
3.  [cite_start]**Layer 3 (NLTK Fallback)**: A statistical Named Entity Recognition (NER) fallback using NLTK to catch standalone names and entities missed by the regex layers[cite: 22, 50].

---

## 📊 Performance Metrics

[cite_start]Validated using synthetic legal Memorandums of Understanding (MoUs), commercial lease agreements, and corporate onboarding forms, Digital Bleach achieved the following results[cite: 48, 63, 65, 66]:

| Model Layer | Accuracy | Precision | Recall |
| :--- | :--- | :--- | :--- |
| **Layer 1 (Regex)** | 100% | 100% | 100% |
| **Layer 2 (Prose Name)** | 94% | 92% | 95% |
| **Layer 3 (NER Fallback)** | 91% | 89% | 92% |

---

## 🛠 Features

- **In-App Rule Manager**: A built-in JSON configuration editor allows users to update PII patterns, stop-words, and keywords directly from the browser with instant engine re-initialization.
- **Pre-Compiled Throughput**: All regex patterns are pre-compiled on initialization to ensure sub-second processing speeds.
- **Memory Optimization**: Employs aggressive garbage collection and session-state caching to support deployment on resource-constrained cloud environments.
- **Zero-Trust & Local**: 100% local processing. [cite_start]No data ever leaves the environment, ensuring complete compliance with enterprise privacy standards[cite: 28, 68, 69].

---

## 📂 Repository Structure

- [cite_start]`app.py`: Streamlit frontend featuring real-time side-by-side visualization and the Advanced Configuration Manager[cite: 23, 52].
- [cite_start]`redactor.py`: The core hybrid NLP engine utilizing PyMuPDF (`fitz`) for geometric coordinate mapping[cite: 51, 58, 59].
- [cite_start]`rules.json`: Centralized configuration for global PII patterns and non-PII labels[cite: 56].
- [cite_start]`requirements.txt`: Project dependencies (Streamlit, PyMuPDF, NLTK)[cite: 50, 51, 52].

---

## 🏃 Local Setup

1.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

2.  **Run the Application**:
    ```bash
    streamlit run app.py
    ```

---

## ⚙️ Customization

Digital Bleach is currently optimized for international and Indian compliance standards, including patterns for:
- **Global**: Emails and International Phone formats.
- **United States**: Social Security Numbers (SSN).
- [cite_start]**India**: PAN Cards and Aadhaar Numbers[cite: 7].

To add new patterns, use the **Advanced Configuration** expander in the UI or manually update `rules.json`.

---