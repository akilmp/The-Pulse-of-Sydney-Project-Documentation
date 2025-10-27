.PHONY: features

features:
	python -m src.features.make_geometries
	python -m src.features.engineer_commute_features
	python -m src.features.engineer_weather_features
	python -m src.features.composite_index
