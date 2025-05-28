from langchain_community.llms import LlamaCpp
from utils import ModelLoader, DatabaseManager

class QueryHandler:
    def __init__(self):
        self.llm = ModelLoader.load_llama()
        self.db = DatabaseManager()

    async def process(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.message.text
        try:
            response = self._generate_response(query)
            await update.message.reply_text(response)
        except Exception as e:
            await update.message.reply_text(f"Error processing query: {str(e)}")

    def _generate_response(self, query: str) -> str:
        if self._is_simple_query(query):
            return self._handle_simple_query(query)
        return self._handle_complex_query(query)

    def _handle_complex_query(self, query: str) -> str:
        return self.db.query_with_llm(self.llm, query)