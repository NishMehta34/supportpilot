"""Local development repositories; replace with tenant-aware DB in Day 22+."""
from uuid import uuid4

class InMemoryRepository:
    def __init__(self):
        self.threads = {}
        self.documents = {}

    def create_thread(self, tenant_id, user_id, title):
        item = {'thread_id': uuid4().hex, 'tenant_id': tenant_id, 'user_id': user_id, 'title': title}
        self.threads[item['thread_id']] = item
        return item

    def get_thread(self, thread_id, tenant_id, user_id):
        item = self.threads.get(thread_id)
        if item is None or (item['tenant_id'], item['user_id']) != (tenant_id, user_id):
            return None
        return item

    def list_threads(self, tenant_id, user_id):
        return [v for v in self.threads.values() if (v['tenant_id'], v['user_id']) == (tenant_id, user_id)]

    def create_document(self, tenant_id, user_id, title, content):
        item = {'document_id': uuid4().hex, 'tenant_id': tenant_id, 'user_id': user_id,
                'title': title, 'content': content}
        self.documents[item['document_id']] = item
        return {k: v for k, v in item.items() if k != 'content'}

    def list_documents(self, tenant_id, user_id):
        return [{k: v for k, v in d.items() if k != 'content'} for d in self.documents.values()
                if (d['tenant_id'], d['user_id']) == (tenant_id, user_id)]
