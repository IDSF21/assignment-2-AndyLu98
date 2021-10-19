import streamlit as st
import pandas as pd
import numpy as np
import plotly.offline as py
import plotly.express as px
import geopandas as gpd
import random
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import datetime

random.seed(0)
st.set_page_config(layout="wide")
st.title('Energy Production and the Road to Renewable')

st.write("Energy production and consumption accounts for almost 75% of all global emissions. Given the urgent need to cut down emissions and transition to renewable energy, it is important to understand and explore this topic further. Let's explore the following questions:")
st.write("1. Where do countries get their energy from?")
st.write("2. Are countries starting the transition to renewable energy production? If so, when did the transition start?")
st.write("3. Does public opinion on climate change have an impact on the transition to renewable energy production?")

power_plant_data_set = "global_power_plant_database.csv"
public_opinion_data_set = "public_opinion.csv"

color_dict ={'(?)':'#708092', 'Oil':'#343540','Hydro':'#1F66E5','Coal':'#A89B8D','Nuclear':'#C74848',\
'Gas':'#7F1ED9','Wind':'#20AEB2','Other':'#6BBDB7','Solar':'#FFDB1A', 'Waste':'#D9D932', 'Petcoke':'#212124',\
'Biomass':'#9DE381', 'Wave and Tidal':'#ACBEE8','Geothermal' :'#7D400A', 'Cogeneration':'#ABAFC7'}


def load_data():
	data = pd.read_csv(power_plant_data_set)
	return data

def clean_data(data):
	data = data[data["primary_fuel"] != 'Storage']
	world = gpd.read_file(gpd.datasets.get_path('naturalearth_lowres'))
	#Based on my research, most of the wind farms are commissioned between 2000 and 2018.
	#Therefore, when there is a wind farm that is missing a commissioned date, I will 
	#fill it with a random value between 2000 and 2018 since the dataset only covers up to 2018. 
	#Similarly, solar farms started to take off between 2010 and now, so when there is a solar farm that 
	#is missing a commissioned date, I will fill it with a random value between 2010 and 2018.
	#Most of the nuclear reactors are built from 1980 - 2015. A random value will be chosen between that range. 
	data['cleaned_commissioning_year'] = data.apply(lambda row: row["commissioning_year"] if not (row["primary_fuel"] == "Wind" and np.isnan(row["commissioning_year"])) else random.randint(2000, 2018), axis=1)
	data['cleaned_commissioning_year'] = data.apply(lambda row: row["cleaned_commissioning_year"] if not (row["primary_fuel"] == "Solar" and np.isnan(row["commissioning_year"])) else random.randint(2010, 2018), axis=1)
	data['cleaned_commissioning_year'] = data.apply(lambda row: row["cleaned_commissioning_year"] if not (row["primary_fuel"] == "Nuclear" and np.isnan(row["commissioning_year"])) else random.randint(1980, 2015), axis=1)
	#This part where we are merging the dataset with another dataset to obtain continent information is adopted from:
	#https://www.kaggle.com/josephchingchunchen/visualizing-power-generation-around-the-globe.
	world = world[['iso_a3','continent']]
	data = data.merge(world, how = 'left',left_on = 'country',right_on = 'iso_a3')
	continent_map = {'Bahrain':'Asia','Cape Verde':'Africa','France':'Europe','French Guiana':'South America','Kosovo':'Europe','Mauritius':'Africa','Norway':'Europe','Singapore':'Asia'}
	for key,val in continent_map.items():
		data.loc[data.country_long==key,'continent'] = val
	return data


def main():
	data = load_data()
	data = clean_data(data)


	#Question 1: 
	country_and_fuel=data.pivot_table(index=['country_long','primary_fuel'],values=['capacity_mw'],aggfunc=np.sum)
	country_and_fuel = country_and_fuel.reset_index()
	all_countries = country_and_fuel['country_long']
	countries = list(set(all_countries))
	countries.sort()

	st.header('Where does energy come from for each country?')
	st.write("Here is a comparison of each country and continent's major power sources. Click each rectangle for more details.")
	#First saw this type of chart at 
	#https://www.kaggle.com/josephchingchunchen/visualizing-power-generation-around-the-globe.
	fig1 = px.treemap(data, path=[px.Constant('world'),'continent','country_long', 'primary_fuel'], values='capacity_mw',
					  color='primary_fuel',color_discrete_map =color_dict)
	st.plotly_chart(fig1, use_container_width=False, sharing='streamlit')

	st.write("As we see, fossil-fuel-powered power plants, such as gas and coal plants, are still dominating world energy production today.")
	
	st.write("You can check the energy sources of each country here")
	option = st.selectbox("Select a country to check where it gets its energy from", countries)
	temp = country_and_fuel[country_and_fuel["country_long"] == option]
	fig2 = px.pie(temp, values='capacity_mw', names='primary_fuel', title='Energy Composition of ' + option, hole=.3)
	st.plotly_chart(fig2, use_container_width=False, sharing='streamlit')

	#Question 2: 
	st.header('Are countries starting to transition to greener energy production?')
	st.write("Next let us explore what type of power plants countries are commissioning each year. This does not include all the\
		countries since some commissioning date are missing.")
	st.write("Only countries where 2/3 or more of the power plants contain a commissioning year are included.")

	countries_commissioning = data[data["cleaned_commissioning_year"].notna()]
	countries_name = data["country_long"].unique()
	for country in countries_name:
		if len(countries_commissioning[countries_commissioning["country_long"] == country]) < 0.667 * len(data[data["country_long"] == country]):
			countries_commissioning = countries_commissioning[countries_commissioning["country_long"] != country]

	country_list_for_commissioning = list(countries_commissioning["country_long"].unique())

	options = st.multiselect('Choose a country or countries to check or compare commission history. Please avoid selecting more than 2 at the same time due to space constraints. ', country_list_for_commissioning, ['United States of America'])

	if len(options) > 0:
		abc = [3 for i in range(len(options))]

		temp = st.columns(abc)

		for i in range(len(options)):
			with temp[i]:
				#st.write()

				data_country = data[data["country_long"] == options[i]] 

				data_country = data_country[data_country["primary_fuel"] != "Storage"]

				data_country = data_country[data_country["cleaned_commissioning_year"].notna()]

				data_country["cleaned_commissioning_year"] = data_country["cleaned_commissioning_year"].astype(int)
				data_country = data_country.groupby(["cleaned_commissioning_year","primary_fuel"])["capacity_mw"].sum().reset_index()

				fig3 = px.bar(data_country, x="cleaned_commissioning_year", y="capacity_mw", color="primary_fuel", color_discrete_map = color_dict)
				fig3.update_xaxes(title_text="Commissioning Year")
				fig3.update_yaxes(title_text="Capacity (mw)")
				fig3.update_layout(title = options[i] + " Power Plant Commissioning History", legend_title="Fuel Type")
				st.plotly_chart(fig3, use_container_width=True, sharing='streamlit')

	st.header('Global trend in the green transition')

	st.write("After checking each country's commission history, let's check the global aggregate trend in power plant commissioning.")

	end_year = st.slider('Year Range', 1907, 2018, 2018)

	#This part where we are processing the dataset to obtain 10-year moving average is adopted from:
	#https://www.kaggle.com/josephchingchunchen/visualizing-power-generation-around-the-globe.
	df2 = data.dropna(subset=['cleaned_commissioning_year']).sort_values('cleaned_commissioning_year')
	global_trend = pd.pivot_table(df2,values = 'capacity_mw',index = ['cleaned_commissioning_year'],columns = 'primary_fuel', aggfunc=np.sum).fillna(0)
	global_trend.reset_index(level=['cleaned_commissioning_year'],inplace=True)
	global_trend['cleaned_commissioning_year'] = pd.to_datetime(global_trend['cleaned_commissioning_year'],format = '%Y')
	#########

	global_trend = global_trend[global_trend["cleaned_commissioning_year"] <= datetime.datetime(year=end_year, month=1, day=1)]
	global_trend = global_trend.groupby('cleaned_commissioning_year').sum()
	for f in global_trend.columns:
		global_trend[f+'_10 Year Moving Average'] = global_trend[f].rolling(10).mean()
	global_trend.reset_index(level=['cleaned_commissioning_year'],inplace=True)

	fig4 = px.line(global_trend,x = 'cleaned_commissioning_year',y =['Coal_10 Year Moving Average','Hydro_10 Year Moving Average','Nuclear_10 Year Moving Average','Gas_10 Year Moving Average','Solar_10 Year Moving Average','Wind_10 Year Moving Average'],
		 labels=dict(commissioning_year="Commissioning Year", value="10 Year Moving Average of Capacity (mw)" ))

	fig4.update_layout(legend_title="")
	fig4.update_xaxes(title_text="Commissioning Year")
	st.plotly_chart(fig4, use_container_width=True, sharing='streamlit')

	st.write("Luckily, it seems like the explosive growth of fossil-fuel-powered power plants has come to an end. Solar and wind farms have started to take off recently.")

	#Question 3: 
	st.header("Does public opinions toward climate change affect where a country wants to get its power from?")
	st.header('USA: A Case Study')
	st.write("Next, let\'s explore whether there is a correlation between public opinion and the type of power plants commissioned.")
	st.write('Although this dataset contains the majority of power plants around the world, there are still many that are missing information. \
		The information on the USA, on the other hand, is relatively comprehensive, which makes it suitable for further analysis. Public opinion polls are also more accessible for the USA. ')
	st.write("The public opinion polls are retrieved from: https://www.aei.org/research-products/report/aei-public-opinion-study-polls-on-the-environment-energy-global-warming-and-nuclear-power-2/ and https://www.pewresearch.org/fact-tank/2019/04/18/a-look-at-how-people-around-the-world-view-climate-change/ft_19-04-18_climatechangeglobal_since2013concerns/")
	public_opinion_trends = ['Knows about climate change very well or fairly well','Worry about climate change a great deal or fair amount', 'Believe that global warming will be a serious problem','Climate change is major threat to our country']
	
	public_opinion_trends_color_dict = {'Knows about climate change very well or fairly well': '#d40d3b','Worry about climate change a great deal or fair amount':'#0eebe7', 'Believe that global warming will be a serious problem':'#0ee83a','Climate change is major threat to our country':'#151417'}
	usa_public_opinion_data = pd.read_csv(public_opinion_data_set)

	opinion_trends_selected = st.multiselect('Choose one or more trends in public opinion regarding climate change', public_opinion_trends, "Knows about climate change very well or fairly well", key = "abc")

	data_USA = data[data["country"] == "USA"] 
	data_USA = data_USA[data_USA["primary_fuel"] != "Storage"]
	data_USA = data_USA[data_USA["cleaned_commissioning_year"].notna()]
	data_USA["cleaned_commissioning_year"] = data_USA["cleaned_commissioning_year"].astype(int)
	data_USA = data_USA.groupby(["cleaned_commissioning_year","primary_fuel"])["capacity_mw"].sum().reset_index()

	fig5 = make_subplots(specs=[[{"secondary_y": True}]])

	for t in data_USA['primary_fuel'].unique():
		temp = data_USA[data_USA['primary_fuel'] == t]
		fig5.add_trace(go.Bar(
			x= temp['cleaned_commissioning_year'], 
			y = temp['capacity_mw'], 
			name=t,
			opacity=0.5,
			marker_color=color_dict[t]),
		secondary_y=False,)


	for trend in opinion_trends_selected:

		fig5.add_trace(
			go.Line(
				x=usa_public_opinion_data['Year'],
				y=usa_public_opinion_data[trend],
				mode='lines',
				name = trend, 
				connectgaps=True,
				marker_color = public_opinion_trends_color_dict[trend]
			),
			secondary_y=True,
		)
	
	fig5.update_layout(barmode='stack')

	fig5.update_xaxes(title_text="Commissioning Year")
	fig5.update_yaxes(title_text="Capacity (mw)", secondary_y=False)
	fig5.update_yaxes(title_text="Percentage of Americans", secondary_y=True)

	st.plotly_chart(fig5, use_container_width=True, sharing='streamlit')


if __name__ == "__main__":
	main()