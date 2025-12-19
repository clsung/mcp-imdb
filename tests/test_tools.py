import pytest
from unittest.mock import MagicMock
from mcp_imdb.tools import (
    search_imdb,
    get_movie_details,
    get_actor_details,
    search_people,
    normalize_imdb_id,
    normalize_person_id,
    ia,
)

@pytest.fixture
def mock_cinemagoer(mocker):
    # Mock the ia object methods
    mocker.patch.object(ia, 'search_movie')
    mocker.patch.object(ia, 'get_movie')
    mocker.patch.object(ia, 'get_person')
    mocker.patch.object(ia, 'search_person')
    return ia

@pytest.mark.asyncio
async def test_search_imdb(mock_cinemagoer):
    # Setup mock return value
    mock_movie = MagicMock()
    mock_movie.movieID = "1375666"
    mock_movie.get.return_value = "Inception"
    mock_cinemagoer.search_movie.return_value = [mock_movie]

    # Test movie search
    response = await search_imdb("Inception")
    assert len(response.results) > 0
    assert response.results[0].imdb_id == "tt1375666"

@pytest.mark.asyncio
async def test_get_movie_details(mock_cinemagoer):
    # Setup mock return value
    mock_movie = MagicMock()

    # Configure dictionary-like behavior
    movie_data = {
        'title': 'Inception',
        'year': 2010,
        'director': [{'name': 'Christopher Nolan'}],
        'cast': [{'name': 'Leonardo DiCaprio'}],
        'plot': ['A thief who steals corporate secrets...::Author'],
        'runtimes': ['148'],
        'rating': 8.8,
        'genres': ['Action', 'Sci-Fi']
    }

    mock_movie.get.side_effect = lambda k, default=None: movie_data.get(k, default)
    mock_movie.__getitem__.side_effect = lambda k: movie_data[k]
    mock_movie.__contains__.side_effect = lambda k: k in movie_data

    mock_cinemagoer.get_movie.return_value = mock_movie

    # Test with Inception's IMDB ID
    movie = await get_movie_details("tt1375666")
    assert movie.title == "Inception"
    assert movie.director == "Christopher Nolan"
    assert movie.year == "2010"

@pytest.mark.asyncio
async def test_get_actor_details(mock_cinemagoer):
    # Setup mock return value
    mock_person = MagicMock()

    person_data = {
        'name': 'Leonardo DiCaprio',
        'birth date': '1974-11-11',
        'birth place': 'Los Angeles, California, USA',
        'filmography': {'actor': []}
    }

    mock_person.get.side_effect = lambda k, default=None: person_data.get(k, default)
    mock_person.__getitem__.side_effect = lambda k: person_data[k]
    mock_person.__contains__.side_effect = lambda k: k in person_data

    mock_cinemagoer.get_person.return_value = mock_person

    # Test with Leonardo DiCaprio's IMDB ID
    actor = await get_actor_details("nm0000138")
    assert actor.name == "Leonardo DiCaprio"
    assert actor.url == "https://www.imdb.com/name/nm0000138/"

@pytest.mark.asyncio
async def test_search_people(mock_cinemagoer):
    # Setup mock return value
    mock_person = MagicMock()
    mock_person.personID = "0000138"
    mock_person.get.return_value = "Leonardo DiCaprio"
    mock_cinemagoer.search_person.return_value = [mock_person]

    response = await search_people("Leonardo DiCaprio")
    assert len(response.results) > 0
    assert response.results[0].imdb_id == "nm0000138"

@pytest.mark.asyncio
async def test_error_handling(mock_cinemagoer):
    # Mock exception
    mock_cinemagoer.get_movie.side_effect = Exception("Not found")

    # Test invalid movie ID
    with pytest.raises(RuntimeError):
        await get_movie_details("invalid_id")
    
    mock_cinemagoer.get_person.side_effect = Exception("Not found")
    # Test invalid person ID
    with pytest.raises(RuntimeError):
        await get_actor_details("invalid_id")

# test normalize_imdb_id
@pytest.mark.asyncio
async def test_normalize_imdb_id():
    assert normalize_imdb_id("tt1375666") == "tt1375666"
    assert normalize_imdb_id("1375666") == "tt1375666"

# test normalize_person_id
@pytest.mark.asyncio
async def test_normalize_person_id():
    assert normalize_person_id("nm0000138") == "nm0000138"
    assert normalize_person_id("0000138") == "nm0000138"
