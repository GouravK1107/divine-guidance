# Divine Guidance

> AI-powered spiritual guidance using **RAG (Retrieval-Augmented Generation)** to provide thoughtful, practical reflections grounded in the teachings of the **Bhagavad Gita**, **Quran**, and **Bible**.

---

## 📖 About the Project

**Divine Guidance** is a Django-based web application that lets users ask life's questions and receive thoughtful, scripture-grounded reflections. Instead of generic AI responses, it uses a Retrieval-Augmented Generation (RAG) pipeline to fetch relevant passages from the Bhagavad Gita, Quran, and Bible, and then generates a contextual, practical answer rooted in those teachings.

The goal is to bridge timeless spiritual wisdom with modern AI, offering guidance that feels personal, respectful of all three traditions, and grounded in actual scripture rather than generic self-help advice.

---

## ✨ Features

- 🙏 Ask any life question and get guidance rooted in real scripture
- 📚 Draws from three major spiritual texts — Bhagavad Gita, Quran, and Bible
- 🔍 Retrieval-Augmented Generation (RAG) pipeline for context-accurate responses
- 🧠 LLM-powered reflection generation on top of retrieved passages
- 🔔 In-app and browser notifications when guidance is ready
- 🌐 Simple, clean web interface built with Django templates
- ⚡ Modular Django app structure for easy extension (more texts/traditions can be added)

---

## 🛠️ Tech Stack

| Layer              | Technology                      |
|---------------------|----------------------------------|
| Backend             | Python, Django                  |
| RAG / Retrieval     | Vector embeddings + similarity search *(e.g. FAISS / ChromaDB — update as per implementation)* |
| LLM                 | *(e.g. OpenAI / Gemini API — update as per implementation)* |
| Frontend            | Django Templates, HTML, CSS, JS |
| Database            | SQLite *(default Django DB — update if changed)* |

> ⚠️ Note: Update the RAG/LLM/Database rows above with the exact libraries and APIs actually used in this project.

---

## 📁 Project Structure

```
divine-guidance/
├── Gyanai/          # Django project configuration (settings, urls, wsgi/asgi)
├── guidance/         # Core app handling guidance requests & responses
├── rag/               # Retrieval-Augmented Generation logic (embeddings, retrieval, generation)
├── static/           # Static assets (CSS, JS, images)
├── templates/         # HTML templates for the web interface
├── manage.py          # Django management script
└── .gitignore
```

---

## 🚀 Getting Started

### Prerequisites

- Python 3.x installed
- pip / virtualenv
- An API key for the LLM provider you're using *(if applicable)*

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/GouravK1107/divine-guidance.git
   cd divine-guidance
   ```

2. **Create and activate a virtual environment**
   ```bash
   python -m venv venv
   # Windows
   venv\Scripts\activate
   # macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   Create a `.env` file in the project root and add:
   ```
   SECRET_KEY=your_django_secret_key
   LLM_API_KEY=your_llm_api_key
   ```

5. **Apply migrations**
   ```bash
   python manage.py migrate
   ```

6. **Run the development server**
   ```bash
   python manage.py runserver
   ```

7. Open your browser and go to:
   ```
   http://127.0.0.1:8000/
   ```

---

## 💡 Usage

1. Open the app in your browser.
2. Type in your question or the situation you're seeking guidance on.
3. The RAG pipeline retrieves the most relevant passages from the Gita, Quran, and Bible.
4. The app generates a thoughtful, practical reflection based on those passages.
5. Read your personalized guidance response.

---

## 🗺️ Roadmap

- [ ] Add more spiritual/philosophical texts
- [ ] Multi-language support
- [ ] User accounts to save past reflections
- [ ] Improve retrieval accuracy with better embeddings
- [ ] Deploy live demo

---

## 🤝 Contributing

Contributions are welcome! If you'd like to improve this project:

1. Fork the repository
2. Create a new branch (`git checkout -b feature/your-feature`)
3. Commit your changes (`git commit -m "Add some feature"`)
4. Push to the branch (`git push origin feature/your-feature`)
5. Open a Pull Request

---

## 👤 Author

**Gourav Kumar**
GitHub: [@GouravK1107](https://github.com/GouravK1107)

---

⭐ If you find this project meaningful, consider giving it a star!
