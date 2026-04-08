import csv
import math

class CityGraph:
    #store city name and populate position and edge
    def __init__(self, coordinates_file: str, adjacencies_file: str) -> None:
        self.positions: dict[str, tuple[float, float]] = {}
        self.edges: dict[str, list[str]] = {}
        self._load_coordinates(coordinates_file)
        self._load_adjacencies(adjacencies_file)

    #read csv and maps city name to its coord, initializes empty neighbor list for city in edges
    def _load_coordinates(self, filepath: str) -> None:
        with open(filepath) as csv_file:
            for row in csv.reader(csv_file):
                city, latitude, longitude = row[0].strip(), float(row[1]), float(row[2])
                self.positions[city] = (latitude, longitude)
                self.edges[city] = [] #empty neighbor list for city

    #read adjacency file and create bidirectional edge list, adds both directions, if A->B, B->A
    def _load_adjacencies(self, filepath: str) -> None:
        with open(filepath) as adjacency_file:
            for line in adjacency_file:
                parts = line.strip().split() #split into list of city names
                if len(parts) < 2:
                    continue
                city, neighbors = parts[0], parts[1:] #remaining token are neighbors
                for neighbor in neighbors:
                    self.edges.setdefault(city, [])
                    self.edges.setdefault(neighbor, [])
                    if neighbor not in self.edges[city]:
                        self.edges[city].append(neighbor)
                    if city not in self.edges[neighbor]: #reverse
                        self.edges[neighbor].append(city)

    #euclidean distance between cities with latitude/longitude, heuristic
    def distance(self, city_a: str, city_b: str) -> float:
        latitude1, longitude1 = self.positions[city_a]
        latitude2, longitude2 = self.positions[city_b]
        return math.sqrt((latitude1 - latitude2) ** 2 + (longitude1 - longitude2) ** 2)

    #return list of neighboring cities or empty list
    def neighbors(self, city: str) -> list[str]:
        return self.edges.get(city, [])

    def all_cities(self) -> list[str]:
        return list(self.positions.keys())
