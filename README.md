# NER数据标注工具

这是一个用于命名实体识别（NER）任务的数据标注工具，基于Streamlit构建，提供简易的前端界面，支持数据的导入、标注和导出。

## 项目结构

```
ner_label
├── app.py                     # 应用程序的入口文件
├── src
│   ├── utils
│   │   ├── annotation.py      # 定义AnnotationManager类，管理标注实体
│   │   └── mapping.py         # 定义VocabularyMapper类，管理词表和映射功能
│   └── example_data
│       └── sample_data.csv    # 示例数据文件，包含“query”列
├── requirements.txt           # 项目所需的Python库和依赖项
└── README.md                  # 项目的文档
```

## 功能

- **数据导入**：支持上传包含“query”列的CSV或Excel文件。
- **实体标签管理**：用户可以添加和删除实体标签，如品牌、品类等。
- **实体标注**：用户可以通过输入文本或选择文本的方式对“query”中的实体进行标注。
- **词表映射**：标注的实体可以与上传的词表进行映射，提供更好的数据管理。
- **数据导出**：支持将标注结果导出为CSV文件。

## 使用方法

1. 克隆或下载项目到本地。
2. 安装所需的依赖项：
   ```
   pip install -r requirements.txt
   ```
3. 运行应用程序：
   ```
   streamlit run app.py
   ```
4. 在浏览器中打开应用程序，按照界面提示上传数据文件和词表，进行实体标注。

## 示例数据

项目中包含一个示例数据文件 `src/example_data/sample_data.csv`，可以用于测试和演示数据标注功能。该文件包含一列名为“query”的文本数据。

## 贡献

欢迎任何形式的贡献！如果您有建议或发现问题，请提交问题或拉取请求。