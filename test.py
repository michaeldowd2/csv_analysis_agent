csv_path = 'https://people.sc.fsu.edu/~jburkardt/data/csv/homes.csv'
chart_path = 'D:\\git\\csv_analysis_agent\\output\\92a62a75-e3c5-4619-8b87-46eff2348613.png'
import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv(csv_path)
average_price_3_bed = df[df[' "Beds"'] == 3]['Sell'].mean()
print(f"On average, 3 bed houses sell for: ${average_price_3_bed:.2f}")

# Create a bar chart to visualize the average price of 3 bed houses
plt.figure(figsize=(8, 5))
plt.bar(['3 Bed Houses'], [average_price_3_bed], color='blue')
plt.title('Average Selling Price of 3 Bed Houses')
plt.ylabel('Average Selling Price ($)')
plt.tight_layout()
plt.savefig(chart_path)