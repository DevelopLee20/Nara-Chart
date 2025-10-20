
import pandas as pd
import httpx
import asyncio
from datetime import datetime

class BidDataUploader:
    """
    엑셀 파일에서 입찰 데이터를 읽어 API를 통해 업로드하는 클래스
    """

    def __init__(self, base_url: str = "http://127.0.0.1:8000"):
        self.base_url = base_url.rstrip('/')
        self.api_endpoint = f"{self.base_url}/api/bids/"
        self.column_mapping = {
            "번호": None,  # 무시 (자동 생성)
            "타입": "bid_type",
            "참가마감": "participation_deadline",
            "투찰마감": "bid_deadline",
            "입찰일": "bid_date",
            "발주기관": "organization",
            "공고명": "title",
            "공고번호": "bid_number",
            "업종": "industry",
            "지역": "region",
            "추정가격": "estimated_price",
            "기초금액": "base_price",
            "1순위업체": "first_rank_company",
            "낙찰금액": "winning_price",
            "기초/낙찰": "base_winning_rate",
            "추정/낙찰": "estimated_winning_rate",
        }

    def _preprocess_data(self, df: pd.DataFrame) -> list[dict]:
        """
        데이터프레임을 API 스키마에 맞게 전처리합니다.
        """
        # None이 아닌 컬럼만 필터링 (번호 컬럼 등 무시할 컬럼 제외)
        filtered_mapping = {k: v for k, v in self.column_mapping.items() if v is not None}

        # 컬럼명 변경
        df = df.rename(columns=filtered_mapping)

        # None으로 매핑된 컬럼 삭제 (예: 번호)
        cols_to_drop = [k for k, v in self.column_mapping.items() if v is None and k in df.columns]
        if cols_to_drop:
            df = df.drop(columns=cols_to_drop)

        # 필수 컬럼 확인
        required_cols = ["title", "bid_number"]
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            # 원본 컬럼명 표시
            original_names = [k for k, v in filtered_mapping.items() if v in missing_cols]
            raise ValueError(
                f"필수 컬럼이 누락되었습니다.\n"
                f"누락된 컬럼: {missing_cols}\n"
                f"엑셀 파일에 필요한 컬럼: {original_names}\n"
                f"현재 엑셀 컬럼: {list(df.columns)}"
            )

        # 날짜 컬럼 포맷 변경
        date_cols = ["participation_deadline", "bid_deadline", "bid_date"]
        for col in date_cols:
            if col in df.columns:
                def parse_date(val):
                    """날짜 파싱 헬퍼: 다양한 형식 처리"""
                    if pd.isna(val):
                        return None

                    # 문자열로 변환
                    date_str = str(val).strip()
                    if not date_str:
                        return None

                    try:
                        # "24-01-18 11:00" 또는 "24-01-18" 형식 처리
                        # 공백이나 시간이 있으면 날짜 부분만 추출
                        date_part = date_str.split()[0] if ' ' in date_str else date_str

                        # "-"로 분리
                        parts = date_part.split('-')
                        if len(parts) == 3:
                            year, month, day = parts
                            # 2자리 연도를 4자리로 변환 (00-99 -> 2000-2099)
                            if len(year) == 2:
                                year = f"20{year}"
                            return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
                    except:
                        pass

                    # 위 방법이 실패하면 pandas의 기본 파싱 시도
                    try:
                        parsed = pd.to_datetime(date_str, errors='coerce')
                        if pd.notna(parsed):
                            return parsed.strftime('%Y-%m-%d')
                    except:
                        pass

                    return None

                df[col] = df[col].apply(parse_date)

        # 숫자 컬럼 처리
        numeric_cols = ["estimated_price", "base_price", "winning_price", "base_winning_rate", "estimated_winning_rate"]
        for col in numeric_cols:
            if col in df.columns:
                def clean_numeric(val):
                    """텍스트 형식의 숫자를 정제하여 float로 변환"""
                    if pd.isna(val):
                        return None

                    # 이미 숫자인 경우
                    if isinstance(val, (int, float)):
                        return float(val) if not pd.isna(val) else None

                    # 문자열 처리
                    str_val = str(val).strip()
                    if not str_val or str_val.lower() in ['', 'nan', 'none', 'null', '-']:
                        return None

                    # 쉼표, 공백, 원화 기호 등 제거
                    str_val = str_val.replace(',', '').replace(' ', '').replace('원', '').replace('₩', '').replace('\\', '')

                    try:
                        return float(str_val)
                    except:
                        return None

                df[col] = df[col].apply(clean_numeric)

        # 정의된 컬럼만 선택 (추가 컬럼 제거)
        valid_cols = [v for v in filtered_mapping.values() if v in df.columns]
        df = df[valid_cols]

        # DataFrame 전체의 NaN 값을 Python의 None으로 변환
        # to_dict() 전에 실행해야 JSON 직렬화 오류를 막을 수 있음
        df = df.astype(object).where(df.notna(), None)

        return df.to_dict(orient="records")

    async def upload_from_excel(self, file_path: str):
        """
        엑셀 파일 경로를 받아 데이터를 API에 업로드합니다.
        """
        try:
            df = pd.read_excel(file_path)
        except FileNotFoundError:
            print(f"오류: 파일을 찾을 수 없습니다 - {file_path}")
            return
        except Exception as e:
            print(f"오류: 엑셀 파일을 읽는 중 문제가 발생했습니다 - {e}")
            return

        records = self._preprocess_data(df)
        total = len(records)
        success_count = 0
        fail_count = 0

        print(f"총 {total}개의 데이터를 업로드합니다...")

        async with httpx.AsyncClient() as client:
            for i, record in enumerate(records):
                try:
                    response = await client.post(self.api_endpoint, json=record, timeout=10) 
                    
                    if response.status_code == 201:
                        print(f"({i+1}/{total}) 성공: {record.get('title', '')[:30]}...")
                        success_count += 1
                    elif response.status_code == 409:
                        print(f"({i+1}/{total}) 건너뜀 (이미 존재): {record.get('bid_number')}")
                        fail_count += 1
                    else:
                        print(f"({i+1}/{total}) 실패: {record.get('title', '')[:30]}... (상태 코드: {response.status_code})")
                        print(f"  - 응답: {response.text}")
                        fail_count += 1

                except httpx.RequestError as e:
                    print(f"({i+1}/{total}) 실패: API 요청 중 오류 발생 - {e}")
                    fail_count += 1
                
                await asyncio.sleep(0.1) # 부하 감소를 위한 약간의 딜레이

        print("\n--- 업로드 완료 ---")
        print(f"성공: {success_count}건")
        print(f"실패/건너뜀: {fail_count}건")


async def main():
    """
    사용 예시:
    1. `BidDataUploader` 인스턴스 생성
    2. `upload_from_excel` 메소드에 엑셀 파일 경로를 전달하여 실행
    """
    # 이 스크립트를 직접 실행할 때 사용되는 예시 코드입니다.
    # 실제 사용 시에는 이 부분을 수정하거나 다른 파일에서 클래스를 import하여 사용하세요.
    
    uploader = BidDataUploader(base_url="http://127.0.0.1:8000")
    excel_file = "your_excel_file.xlsx"
    await uploader.upload_from_excel(excel_file)
    pass

if __name__ == "__main__":
    asyncio.run(main())
    print("BidDataUploader 클래스가 정의되었습니다.")
    print("사용 예시:")
    print("uploader = BidDataUploader()")
    print("asyncio.run(uploader.upload_from_excel('your_excel_file.xlsx'))")
