import unittest
from unittest.mock import MagicMock
from graph_generator import GraphGenerator
from actors_path import ActorToActorPath
from log import log


class TestGraphDecorator(unittest.TestCase):
    def setUp(self):
        self.actor_ids = ["Maxim", "Kostya", "Irina", "Svetlana", "Lilia", "Elena"]
        self.movie_mocks = {
            "Moscow": MagicMock(movieID="Moscow", data={"title": "Moscow, The"}),
            "Sumy": MagicMock(movieID="Sumy", data={"title": "Sumy, The"}),
            "Budapest": MagicMock(movieID="Budapest", data={"title": "Budapest, The"}),
            "New York": MagicMock(movieID="New York", data={"title": "New York, The"}),
        }
        self.persons = dict([
            self.generate_person("Maxim", ["Sumy"]),
            self.generate_person("Kostya", ["Sumy", "Moscow"]),
            self.generate_person("Svetlana", ["Moscow", "New York"]),
            self.generate_person("Irina", ["New York"]),
            self.generate_person("Elena", ["Moscow", "New York", "Budapest"]),
            self.generate_person("Lilia", ["Moscow", "Budapest"]),
        ])
        self.movies = dict([
            self.generate_movie("Sumy", ["Kostya", "Maxim"]),
            self.generate_movie("Moscow", ["Kostya", "Svetlana", "Elena", "Lilia"]),
            self.generate_movie("Budapest", ["Elena", "Lilia"]),
            self.generate_movie("New York", ["Irina", "Svetlana", "Elena"])
        ])

    def generate_person(self, actor_id, movies):
        return (actor_id, {
            "personID": actor_id,
            "data": {
                "name": actor_id,
                "filmography": [{
                    "actor": [self.movie_mocks[m] for m in movies]
                }]
            }
        })

    def generate_movie(self, movie_id, actors):
        return movie_id, {
            "cast": [MagicMock(personID=a) for a in actors],
            "title": movie_id
        }

    def get_person_main(self, actor_id):
        # log.debug("mocking actor: {}".format(actor_id))
        return self.persons[actor_id]

    def get_movie(self, movie_id):
        # log.debug("mocking movie: {}".format(movie_id))
        return self.movies[movie_id]

    def test_family_graph1(self):
        attrs = {
            'get_person_main.side_effect': self.get_person_main,
            'get_movie.side_effect': self.get_movie
        }
        ia = MagicMock(**attrs)
        graph = GraphGenerator(self.actor_ids, ia, max_threads=4).generate()

        self.assertEqual(None, graph.get_edge("Maxim", "Lilia"))
        self.assertEqual({"Sumy"}, graph.get_edge("Maxim", "Kostya"))

        self.assertEqual({"Sumy"}, graph.get_edge("Kostya", "Maxim"))
        self.assertEqual({"Moscow"}, graph.get_edge("Kostya", "Svetlana"))
        self.assertEqual({"Moscow"}, graph.get_edge("Kostya", "Elena"))
        self.assertEqual({"Moscow"}, graph.get_edge("Kostya", "Lilia"))

        self.assertEqual({"Moscow"}, graph.get_edge("Lilia", "Svetlana"))
        self.assertEqual({"Moscow", "Budapest"}, graph.get_edge("Lilia", "Elena"))
        self.assertEqual({"Moscow"}, graph.get_edge("Lilia", "Kostya"))
        self.assertEqual({"Moscow"}, graph.get_edge("Svetlana", "Lilia"))
        self.assertEqual({"Moscow", "New York"}, graph.get_edge("Svetlana", "Elena"))
        self.assertEqual({"Moscow"}, graph.get_edge("Svetlana", "Kostya"))
        self.assertEqual({"New York"}, graph.get_edge("Svetlana", "Irina"))

        self.assertEqual({"Moscow", "Budapest"}, graph.get_edge("Elena", "Lilia"))
        self.assertEqual({"Moscow", "New York"}, graph.get_edge("Elena", "Svetlana"))
        self.assertEqual({"Moscow"}, graph.get_edge("Elena", "Kostya"))
        self.assertEqual({"New York"}, graph.get_edge("Elena", "Irina"))

        self.assertEqual({"New York"}, graph.get_edge("Irina", "Elena"))
        self.assertEqual({"New York"}, graph.get_edge("Irina", "Svetlana"))

    def get_family_graph(self):
        attrs = {
            'get_person_main.side_effect': self.get_person_main,
            'get_movie.side_effect': self.get_movie
        }
        ia = MagicMock(**attrs)
        return GraphGenerator(self.actor_ids, ia, max_threads=1).generate()

    def test_family_search1(self):
        graph = self.get_family_graph()

        expected = ActorToActorPath("Maxim", "Kostya")
        expected.add_connection("Maxim", "Kostya", "Sumy")

        actual = ActorToActorPath.search(graph, "Maxim", "Kostya")
        self.assertEqual(expected, actual)

    def test_family_search2(self):
        graph = self.get_family_graph()

        expected = ActorToActorPath("Maxim", "Elena")
        expected.add_connection("Maxim", "Kostya", "Sumy")
        expected.add_connection("Kostya", "Elena", "Moscow")

        actual = ActorToActorPath.search(graph, "Maxim", "Elena")

        self.assertEqual(expected, actual)

    def test_family_search3(self):
        graph = self.get_family_graph()

        expected = ActorToActorPath("Maxim", "Irina")
        expected.add_connection("Maxim", "Kostya", "Sumy")
        expected.add_connection("Kostya", "Elena", "Moscow")
        expected.add_connection("Kostya", "Svetlana", "Moscow")
        expected.add_connection("Elena", "Irina", "New York")
        expected.add_connection("Svetlana", "Irina", "New York")

        actual = ActorToActorPath.search(graph, "Maxim", "Irina")

        self.assertEqual(expected, actual)

    def test_family_search4(self):
        graph = self.get_family_graph()

        expected = ActorToActorPath("Lilia", "Irina")
        expected.add_connection("Lilia", "Elena", {"Moscow", "Budapest"})
        expected.add_connection("Lilia", "Svetlana", "Moscow")
        expected.add_connection("Elena", "Irina", "New York")
        expected.add_connection("Svetlana", "Irina", "New York")

        actual = ActorToActorPath.search(graph, "Lilia", "Irina")

        self.assertEqual(expected, actual)


if __name__ == '__main__':
    unittest.main()
