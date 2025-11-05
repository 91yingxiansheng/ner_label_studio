class VocabularyMapper:
    def __init__(self):
        self.vocab = {}

    def load_vocabulary(self, vocab_data):
        self.vocab = vocab_data

    def has_vocabulary(self):
        return bool(self.vocab)

    def get_vocabulary_stats(self):
        return {k: len(v) for k, v in self.vocab.items()}

    def find_mappings(self, text, label):
        # 简单匹配：完全相同或包含
        candidates = self.vocab.get(label, [])
        result = [c for c in candidates if text in c or c in text]
        # 如果没有包含关系，返回全部候选
        return result if result else candidates