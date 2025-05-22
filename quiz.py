import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

#1
df = pd.read_csv("서울대기오염_2019.xlsx - Sheet1.csv", encoding="utf-8-sig")

# 분석변수만 추출 및 컬럼명 변경
df = df[["날짜", "측정소명", "미세먼지", "초미세먼지"]]
df.columns = ["date", "district", "pm10", "pm25"]

#결측치 확인 및 제거
df = df[~df["date"].astype(str).str.contains("전체")]
df = df.dropna(subset=["date", "district", "pm10", "pm25"])

# 자료형 변환
df["date"] = pd.to_datetime(df["date"])
df["pm10"] = pd.to_numeric(df["pm10"], errors="coerce")
df["pm25"] = pd.to_numeric(df["pm25"], errors="coerce")
df = df.dropna(subset=["pm10", "pm25"])

# 이상치 제거 (PM10은 0~300 사이가 대부분 적절)
df = df[(df["pm10"] >= 0) & (df["pm10"] <= 300)]

#2 month, day 파생변수 생성
df["month"] = df["date"].dt.month
df["day"] = df["date"].dt.day

# 계절(season) 변수 생성
def get_season(month):
    if month in [3, 4, 5]:
        return "spring"
    elif month in [6, 7, 8]:
        return "summer"
    elif month in [9, 10, 11]:
        return "fall"
    else:
        return "winter"

df["season"] = df["month"].apply(get_season)

#3 최종 분석 대상 데이터 확인
final_columns = ["date", "district", "pm10", "pm25", "month", "day", "season"]
final_df = df[final_columns]

# 201906_output.csv로 저장
final_df.to_csv("201906_output.csv", index=False)

#4 전체 데이터 기준 PM10 평균
avg_pm10 = df["pm10"].mean()
print(f"연간 평균 PM10: {avg_pm10:.2f} ug/m^3")

#5 PM10 최댓값이 발생한 날짜, 구 출력
max_pm10 = df["pm10"].max()
max_row = df[df["pm10"] == max_pm10].iloc[0]
print(f"PM10 최댓값 {max_pm10} ug/m^3 발생 날짜: {max_row['date'].date()}, 구: {max_row['district']}")

#6 각 구별 pm10 평균 계산
district_avg = df.groupby("district")["pm10"].mean().reset_index()
district_avg.columns = ["district", "avg_pm10"]

# 상위 5개 구만 출력
top5 = district_avg.sort_values(by="avg_pm10", ascending=False).head(5)
print("구별 PM10 평균 상위 5개:")
print(top5)

#7 계절별 평균 pm10, pm25 동시 출력
season_avg = df.groupby("season")[["pm10", "pm25"]].mean().reset_index()
season_avg.columns = ["season", "avg_pm10", "avg_pm25"]

# 평균값 기준 오름차순 정렬
season_avg_sorted = season_avg.sort_values(by="avg_pm10", ascending=True)
print("계절별 PM10/PM2.5 평균:")
print(season_avg_sorted)

#8 pm10 값을 기준으로 등급 분류 (good/normal/bad/worse)
def pm10_grade(x):
    if x <= 30:
        return "good"
    elif x <= 80:
        return "normal"
    elif x <= 150:
        return "bad"
    else:
        return "worse"

df["pm_grade"] = df["pm10"].apply(pm10_grade)

# 등급별 빈도수 및 비율 계산
grade_counts = df["pm_grade"].value_counts().reset_index()
grade_counts.columns = ["pm_grade", "n"]
grade_counts["pct"] = (grade_counts["n"] / grade_counts["n"].sum() * 100).round(2)
print("PM10 등급별 빈도 및 비율:")
print(grade_counts)

#9 구별 good 등급 비율 계산
good_df = df[df["pm_grade"] == "good"]
district_good = good_df["district"].value_counts().reset_index()
district_total = df["district"].value_counts().reset_index()

district_good.columns = ["district", "n"]
district_total.columns = ["district", "total"]

good_ratio = pd.merge(district_good, district_total, on="district")
good_ratio["pct"] = (good_ratio["n"] / good_ratio["total"] * 100).round(2)

# good 비율 기준 상위 5개 구 출력
top5_good = good_ratio.sort_values(by="pct", ascending=False).head(5)
print(" good 비율 상위 5개 구:")
print(top5_good)

#10 x축: date, y축: pm10 (선그래프)
plt.figure(figsize=(12, 5))
sns.lineplot(data=df, x="date", y="pm10", linewidth=1)
plt.title("Daily Trend of PM10 in Seoul, 2019")
plt.xlabel("Date")
plt.ylabel("PM10 (ug/m^3)")
plt.tight_layout()
plt.show()

# 분석 결과 
# → 봄과 겨울철에 PM10 수치가 뚜렷하게 높아지는 경향이 나타남

#11 계절별 등급 비율 계산
season_grade = df.groupby(["season", "pm_grade"]).size().reset_index(name="n")
season_total = df.groupby("season").size().reset_index(name="total")
season_pct = pd.merge(season_grade, season_total, on="season")
season_pct["pct"] = (season_pct["n"] / season_pct["total"] * 100).round(2)

# 막대그래프 (seaborn barplot)
plt.figure(figsize=(8, 5))
sns.barplot(data=season_pct, x="season", y="pct", hue="pm_grade",
            order=["spring", "summer", "fall", "winter"],
            hue_order=["good", "normal", "bad", "worse"])
plt.title("Seasonal Distribution of PM10 Grades in Seoul, 2019")
plt.ylabel("Rate (%)")
plt.xlabel("Season")
plt.legend(title="PM10 grade")
plt.tight_layout()
plt.show()

# 분석 결과
'''summer(여름)에 good 등급 비율이 가장 높고,
spring/winter에는 bad/worse 등급이 상대적으로 높음'''
