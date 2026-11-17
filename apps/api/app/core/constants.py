"""
Constants and Conversion Tables for GraphRAG Admission Guidance System.
Supports combined admission methods (KET_HOP) and standardized score mappings.
"""

from typing import Dict, Union
from .enums import AdmissionMethod

# Bảng quy đổi điểm IELTS sang thang điểm 10 môn Tiếng Anh (theo quy chế tuyển sinh các trường ĐH)
IELTS_TO_SCORE: Dict[float, float] = {
    5.0: 6.0,
    5.5: 7.0,
    6.0: 8.0,
    6.5: 8.5,
    7.0: 9.0,
    7.5: 9.5,
    8.0: 10.0,
    8.5: 10.0,
    9.0: 10.0,
}


def calculate_combined_score(
    exam_score: float, 
    ielts_score: float, 
    method: Union[AdmissionMethod, str]
) -> float:
    """
    Tính điểm xét tuyển phương thức Kết hợp (Chứng chỉ quốc tế + Điểm thi/Học bạ).
    
    Ví dụ: Thí sinh thi Toán + Văn (2 môn = 17 điểm) kết hợp IELTS 6.5 (quy đổi 8.5)
    -> Điểm xét tuyển = 17 + 8.5 = 25.5
    """
    method_str = method.value if isinstance(method, AdmissionMethod) else str(method)
    
    if method_str in [AdmissionMethod.KET_HOP.value, "Kết hợp", "KET_HOP"]:
        # Tìm mức quy đổi gần nhất (làm tròn xuống nếu điểm nằm giữa các mốc)
        converted = 0.0
        for band in sorted(IELTS_TO_SCORE.keys()):
            if ielts_score >= band:
                converted = IELTS_TO_SCORE[band]
        if converted > 0.0:
            return exam_score + converted

    return exam_score
