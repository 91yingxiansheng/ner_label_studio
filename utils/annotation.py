import pandas as pd
import copy


class AnnotationManager:
    def __init__(self):
        self.annotations = {}

    def initialize_annotations(self, data_len):
        self.annotations = {i: [] for i in range(data_len)}

    def add_annotation(self, idx, annotation):
        # 检查重叠
        for ann in self.annotations.get(idx, []):
            if not (annotation['end'] <= ann['start'] or annotation['start'] >= ann['end']):
                return False  # 有重叠
        self.annotations[idx].append(copy.deepcopy(annotation))
        return True

    def get_annotations(self, idx):
        return self.annotations.get(idx, [])

    def remove_annotation(self, idx, ann_idx):
        if idx in self.annotations and 0 <= ann_idx < len(self.annotations[idx]):
            self.annotations[idx].pop(ann_idx)

    def update_annotation(self, idx, ann_idx, annotation):
        if idx in self.annotations and 0 <= ann_idx < len(self.annotations[idx]):
            self.annotations[idx][ann_idx] = copy.deepcopy(annotation)

    def get_annotation_count(self):
        return sum(1 for anns in self.annotations.values() if anns)

    def export_annotations(self, df):
        # 导出为 DataFrame，每条 query 一行，标注为 json 字符串
        export_df = df.copy()
        export_df['annotations'] = export_df.index.map(
            lambda idx: self.annotations.get(idx, [])
        ).map(lambda x: x if x else [])
        export_df['annotations'] = export_df['annotations'].apply(lambda x: str(x))
        return export_df