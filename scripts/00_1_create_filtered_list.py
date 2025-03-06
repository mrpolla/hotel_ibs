import pandas as pd

# Read the original CSV files
hotel_df = pd.read_csv("./dataset/hotel_info.csv")
chain_df = pd.read_csv("./dataset/chain_info.csv")

# Randomly select 200 hotels from hotel_info.csv.
# The random_state parameter is optional and ensures reproducibility.
filtered_hotel_df = hotel_df.sample(n=200, random_state=42)

print(hotel_df.shape)
print(filtered_hotel_df.shape)
# Save the filtered hotels to a new CSV file
filtered_hotel_df.to_csv("hotel_info_filtered.csv", index=False)

# Get the unique chain IDs from the filtered hotels
relevant_chain_ids = filtered_hotel_df["chain_id"].unique()

# Filter the chains from chain_info.csv based on the selected chain IDs
filtered_chain_df = chain_df[chain_df["chain_id"].isin(relevant_chain_ids)]

# Save the filtered chains to a new CSV file
filtered_chain_df.to_csv("chain_info_filtered.csv", index=False)
