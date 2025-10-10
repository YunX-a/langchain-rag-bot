import pytest
from unittest.mock import patch, MagicMock
from app.services import rag_service

import os
from dotenv import load_dotenv
load_dotenv() # 加载 .env 文件

# 使用 pytest 的 @patch 装饰器来“模拟”整个 create_rag_chain 函数
@patch('app.services.qa_service.create_rag_chain')
def test_query_document_with_mocking(mock_create_rag_chain):
    """
    这是一个单元测试函数，用于测试 query_document 函数。
    它通过模拟 create_rag_chain 的返回值，来隔离对真实 LLM 和文件系统的依赖。
    """
    # 1. 准备 (Arrange)
    # --------------------
    # 定义一个假的、预设好的 RAG 链返回结果
    fake_result = {
        "result": "这是一个来自模拟链的答案",
        "source_documents": [MagicMock(page_content="这是一个模拟的来源文档")]
    }

    # 创建一个模拟的 RAG 链对象
    mock_rag_chain = MagicMock()
    # 配置这个假链，当它的 __call__ 方法（对应 qa_chain({"query": ...})）被调用时，
    # 就返回我们预设好的 fake_result
    mock_rag_chain.return_value = fake_result

    # 配置我们的“模拟函数”，当 create_rag_chain 被调用时，
    # 让它返回我们刚刚创建的 mock_rag_chain 对象
    mock_create_rag_chain.return_value = mock_rag_chain

    # 定义测试用的输入
    test_question = "这是一个测试问题"
    test_file_path = "data/fake_test.pdf"


    # 2. 执行 (Act)
    # -----------------
    # 调用我们真正想要测试的函数
    actual_response = rag_service.query_document(
        question=test_question,
        file_path=test_file_path
    )


    # 3. 断言 (Assert)
    # -----------------
    # 检查函数的返回值是否和我们预期的完全一致
    assert actual_response["answer"] == fake_result["result"]
    assert len(actual_response["source_documents"]) == 1
    assert actual_response["source_documents"][0] == "这是一个模拟的来源文档"

    # 检查我们的模拟函数是否真的被调用了
    mock_create_rag_chain.assert_called_once_with(
    file_path=test_file_path,
    llm_api_key=os.getenv("DEEPSEEK_API_KEY"), # <-- 修改这里
    llm_base_url="https://api.deepseek.com",
    llm_model="deepseek-chat"
    )