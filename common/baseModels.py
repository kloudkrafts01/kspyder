

class Dataset():

    schema: str
    model_name: str
    model: dict
    params: dict
    count: int
    json_dump: str
    csv_dump: str
    scopes: list
    data: list
    failed_items: list

    def __init__(self,schema,model_name,model,params=None,count=0,scopes=None,**kwargs):
        self.schema = schema
        self.model_name = model_name
        self.model = model
        self.params = params
        self.count = count
        self.json_dump = None
        self.csv_dump = None
        self.scopes = scopes
        self.data = []
        self.failed_items = []

    def to_json(self):

        full_dataset = {
            'header': {
                'schema': self.schema,
                'model_name': self.model_name,
                'model': self.model,
                'params': self.params,
                'count': self.count,
                'json_dump': self.json_dump,
                'csv_dump': self.csv_dump,
                'scopes': self.scopes
            },
            'data': self.data,
            'failed_items': self.failed_items
        }

        return full_dataset
    
    def update(self,count=0,data=None):

        if data:
            self.count += count
            self.data.extend(data)
        


