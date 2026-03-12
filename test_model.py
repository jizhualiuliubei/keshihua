import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

def load_and_overview_data(file_path):
    try:
        df=pd.read_csv(file_path,encoding="utf-8-sig")
        print("数据读取成功")
        print("\n1.数据基础信息：")
        print(df.info())

        print("\n2.数值字段统计：")
        print(df.describe())

        print("\n3.缺失值分布:")
        missing_info=df.isnull().sum()/len(df)*100
        print(missing_info[missing_info>0])

        duplicate_count=df.duplicated().sum()
        print(f"\n4.重复记录数：{duplicate_count}")
        return df
    except Exception as e:
        print("数据读取失败")
        return None
df=load_and_overview_data("sales_data.csv")

#数据预处理
def preprocess_data(df):
    df_clean=df.copy()
    print("开始数据预处理")

    #1.重复值处理
    df_clean=df_clean.drop_duplicates()
    print(f"1. 去重后数据量：{len(df_clean)}")

    abnormal_volume=len(df_clean[df_clean["销量"]<0])
    df_clean=df_clean[df_clean["销量"]>=0]
    print(f"2. 过滤异常销量记录数：{abnormal_volume}")

    #按"产品类别"分组，用每个类别各自的平均销售额填充该类别内的缺失值
    df_clean["销售额"]=df_clean.groupby("产品类别")["销售额"].transform(
        lambda x:x.fillna(x.mean())
    )
    print(f"3. 缺失值填充完成，剩余缺失值：{df_clean['销售额'].isnull().sum()}")

    df_clean["日期"]=pd.to_datetime(df_clean["日期"])
    # 新增「月份」字段（方便后续按月份分析）
    df_clean["月份"]=df_clean["日期"].dt.month#dt为访问器（accessor），用于提取日期时间的各种属性
    print("4. 日期格式转换完成，新增「月份」字段")

    #数据类型优化
    df_clean["促销标识"]=df_clean["促销标识"].map({0:"无促销",1:"有促销"})#	使用字典进行映射转换：0→"无促销", 1→"有促销"
    print("5.数据类型优化完成")

    print("数据预处理完成！")

    return df_clean
df_clean=preprocess_data(df)

def analyze_data(df):
    "业务数据分析：计算核心指标"
    print("\n 开始业务数据分析")
    total_sales=df["销售额"].sum()
    total_volume = df["销量"].sum()
    avg_sales_per_product=df.groupby("产品类别")["销售额"].mean().round(2)
    print(f"1. 整体销售额：{total_sales:.2f} 元")
    print(f"   整体销量：{total_volume} 件")
    print(f"   各产品类别平均销售额：\n{avg_sales_per_product}")

    region_sales=df.groupby("区域")["销售额"].sum().sort_values(ascending=False).round(2)
    print(f"\n2. 区域销售额排名：\n{region_sales}")

    promotion_analysis=df.groupby("促销标识")["销售额"].agg(["sum","mean"]).round(2)#agg() 常用聚合函数
    print(f"\n3. 促销效果分析：\n{promotion_analysis}")

    monthly_sales = df.groupby("月份")["销售额"].sum().round(2)
    print(f"\n4. 月度销售额：\n{monthly_sales}")

    # 返回分析结果（用于可视化）
    return {
        "region_sales": region_sales,
        "promotion_analysis": promotion_analysis,
        "monthly_sales": monthly_sales,
        "avg_sales_per_product": avg_sales_per_product
    }

analysis_result=analyze_data(df_clean)


def visualize_data(analysis_result):
    plt.rcParams["font.sans-serif"]=["SimHei"]
    plt.rcParams["axes.unicode_minus"]=False

    fig,((ax1,ax2),(ax3,ax4))=plt.subplots(2,2,figsize=(16,12))
    fig.suptitle("销售数据可视化分析报告", fontsize=16, fontweight="bold")

    ax1.bar(analysis_result["region_sales"].index,analysis_result["region_sales"].values,color="#1f77b4")
    ax1.set_title("各区域销售额",fontsize=12)
    ax1.set_ylabel("销售额（元）")
    ax1.tick_params(axis="x",rotation=45)

    for x, y in enumerate(analysis_result["region_sales"].values):
        ax1.text(x, y + 10000, f"{y:.0f}", ha="center")

    promotion_sum=analysis_result["promotion_analysis"]["sum"]
    ax2.bar(promotion_sum.index, promotion_sum.values, color=["#ff7f0e", "#2ca02c"])
    ax2.set_title("促销/非促销销售额对比", fontsize=12)
    ax2.set_ylabel("销售额（元）")
    for x, y in enumerate(promotion_sum.values):
        ax2.text(x, y + 10000, f"{y:.0f}", ha="center")

    ax3.plot(analysis_result["monthly_sales"].index, analysis_result["monthly_sales"].values,
             marker="o", linewidth=2, color="#d62728")
    ax3.set_title("月度销售额趋势", fontsize=12)
    ax3.set_xlabel("月份")
    ax3.set_ylabel("销售额（元）")
    ax3.set_xticks([1, 2, 3])
    # 数值标注
    for x, y in analysis_result["monthly_sales"].items():
        ax3.text(x, y + 10000, f"{y:.0f}", ha="center")

    ax4.pie(analysis_result["avg_sales_per_product"].values,
            labels=analysis_result["avg_sales_per_product"].index,
            autopct="%1.1f%%", startangle=90, colors=["#9467bd", "#8c564b", "#e377c2", "#7f7f7f"])
    ax4.set_title("各产品类别平均销售额占比", fontsize=12)
    plt.tight_layout()
    plt.savefig("sales_analysis.png", dpi=300, bbox_inches="tight")
    plt.show()

visualize_data(analysis_result)
