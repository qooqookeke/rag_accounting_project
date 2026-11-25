import sys
import json
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

from src.core.retriever import YetaRetriever

# 세무 RAG 리트리버 인스턴스
retriever = YetaRetriever()

def search_yeta_deduction(query: str, top_k: int = 3) -> str:
    """
    [연말정산 세무 지식 검색 도구]
    사용자의 연말정산 질문에 대해 소득세법 조문 및 국세청 공식 FAQ를 검색하여 반환합니다.
    """
    results = retriever.search(query=query, top_k=top_k)
    if not results:
        return "관련된 연말정산 법령이나 해설 문서를 찾지 못했습니다."

    formatted = []
    for r in results:
        formatted.append(
            f"### [{r['rank'] if 'rank' in r else 1}위] {r['law_ref']} ({r['title']}) [유사도: {r['score']*100:.1f}%]\n"
            f"- 카테고리: {r['category']}\n"
            f"- 출처 파일: {r['source']}\n"
            f"- 법률 본문 내용:\n{r['text']}\n"
        )
    return "\n---\n".join(formatted)


# 1. 공식 mcp 패키지가 설치되어 있는 경우 (Python 3.10+ FastMCP 모드)
try:
    from mcp.server.fastmcp import FastMCP
    mcp = FastMCP("Yeta-Tax-RAG")

    @mcp.tool()
    def search_tax_guide(query: str, top_k: int = 3) -> str:
        """연말정산 소득공제 및 세액공제 요건, 한도, 소득세법 조문을 검색합니다."""
        return search_yeta_deduction(query=query, top_k=top_k)

    def run_mcp():
        mcp.run()

except ImportError:
    # 2. mcp 패키지가 없는 환경(Python 3.9)에서도 Claude Desktop/Cursor와 연동 가능한 경량 표준 Stdio 핸들러
    def run_mcp():
        sys.stderr.write("🏛️ Yeta-RAG Stdio Tool Server Started (JSON-RPC Compatible Mode)\n")
        sys.stderr.flush()

        while True:
            try:
                line = sys.stdin.readline()
                if not line:
                    break
                request = json.loads(line)
                req_id = request.get("id")
                method = request.get("method")

                if method == "tools/list":
                    response = {
                        "jsonrpc": "2.0",
                        "id": req_id,
                        "result": {
                            "tools": [
                                {
                                    "name": "search_tax_guide",
                                    "description": "국세청 연말정산 해설서 및 소득세법 조문(월세, 의료비, 교육비, 신용카드 등)을 검색합니다.",
                                    "inputSchema": {
                                        "type": "object",
                                        "properties": {
                                            "query": {"type": "string", "description": "연말정산 질문 키워드"},
                                            "top_k": {"type": "integer", "description": "검색할 문서 수", "default": 3}
                                        },
                                        "required": ["query"]
                                    }
                                }
                            ]
                        }
                    }
                elif method == "tools/call":
                    params = request.get("params", {})
                    args = params.get("arguments", {})
                    query = args.get("query", "")
                    top_k = args.get("top_k", 3)
                    content_str = search_yeta_deduction(query, top_k)
                    response = {
                        "jsonrpc": "2.0",
                        "id": req_id,
                        "result": {
                            "content": [{"type": "text", "text": content_str}]
                        }
                    }
                else:
                    response = {"jsonrpc": "2.0", "id": req_id, "result": {}}

                sys.stdout.write(json.dumps(response) + "\n")
                sys.stdout.flush()
            except Exception as e:
                sys.stderr.write(f"Error: {e}\n")
                sys.stderr.flush()

if __name__ == "__main__":
    run_mcp()
