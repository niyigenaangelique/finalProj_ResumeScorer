import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
import os

try:
    sns.set_theme(style="whitegrid")
    plt.figure(figsize=(6, 4))
    plt.pie([10, 20, 30], labels=['A', 'B', 'C'], autopct='%1.1f%%')
    plt.title('Test Chart')
    plt.savefig('test_chart_output.png')
    plt.close()
    print("Chart saved successfully to test_chart_output.png")
except Exception as e:
    print(f"Error generating chart: {e}")
