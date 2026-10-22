from weather_api_test import fetch_and_store
from services.coastal_data_service import CoastalDataService
from services.risk_assessment_service import RiskAssessmentService
from services.storm_data_service import StormDataService


def main():
    weather_count = fetch_and_store()
    coastal_count = len(CoastalDataService().collect_all())
    storm_count = len(StormDataService().collect_current_cyclones())
    risk_count = len(RiskAssessmentService().assess_all())
    print(
        "Collection complete: "
        f"weather={weather_count}, coastal={coastal_count}, "
        f"storms={storm_count}, risk_assessments={risk_count}"
    )


if __name__ == "__main__":
    main()
