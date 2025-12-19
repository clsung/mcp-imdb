import asyncio
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import logging
from imdb import Cinemagoer
import re
from functools import lru_cache
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("mcp_imdb_client")

# Initialize Cinemagoer
ia = Cinemagoer()

# Cache for movie details
movie_details_cache = {}

# Pydantic models
class SearchRequest(BaseModel):
    query: str = Field(..., description="Search query for IMDB")
    content_type: Optional[str] = Field(None, description="Type of content to search for (movies, tv, etc.)")

class SearchResult(BaseModel):
    title: str
    url: str
    year: Optional[str] = None
    rating: Optional[str] = None
    description: Optional[str] = None
    imdb_id: str
    
    class Config:
        """Configuration for Pydantic model."""
        json_encoders = {
            # Custom encoders if needed
        }
        json_schema_extra = {
            "example": {
                "title": "The Shawshank Redemption",
                "url": "https://www.imdb.com/title/tt0111161/",
                "year": "1994",
                "rating": "9.3",
                "description": "Two imprisoned men bond over a number of years...",
                "imdb_id": "tt0111161"
            }
        }

class SearchResponse(BaseModel):
    results: List[SearchResult]
    total_results: int
    
    class Config:
        """Configuration for Pydantic model."""
        json_encoders = {
            # Custom encoders if needed
        }
        json_schema_extra = {
            "example": {
                "results": [
                    {
                        "title": "The Shawshank Redemption",
                        "url": "https://www.imdb.com/title/tt0111161/",
                        "year": "1994",
                        "rating": "9.3",
                        "description": "Two imprisoned men bond over a number of years...",
                        "imdb_id": "tt0111161"
                    }
                ],
                "total_results": 1
            }
        }

class MovieDetails(BaseModel):
    title: str
    year: Optional[str] = None
    rating: Optional[str] = None
    genres: List[str] = []
    director: Optional[str] = None
    cast: List[str] = []
    plot: Optional[str] = None
    poster_url: Optional[str] = None
    runtime: Optional[str] = None
    imdb_id: str

class ActorDetails(BaseModel):
    """
    Model for actor/actress details from IMDB.
    """
    name: str
    imdb_id: str
    url: str
    birth_date: Optional[str] = None
    birth_place: Optional[str] = None
    death_date: Optional[str] = None
    biography: Optional[str] = None
    photo_url: Optional[str] = None
    height: Optional[str] = None
    filmography: List[Dict[str, Any]] = []
    known_for: List[Dict[str, str]] = []

    class Config:
        """Configuration for Pydantic model."""
        json_encoders = {
            # Custom encoders if needed
        }
        json_schema_extra = {
            "example": {
                "name": "Tom Hanks",
                "imdb_id": "nm0000158",
                "url": "https://www.imdb.com/name/nm0000158/",
                "birth_date": "July 9, 1956",
                "birth_place": "Concord, California, USA",
                "biography": "Thomas Jeffrey Hanks is an American actor and filmmaker...",
                "photo_url": "https://example.com/tom_hanks.jpg",
                "height": "6' 0\" (1.83 m)",
                "filmography": [
                    {"title": "Forrest Gump", "year": "1994", "role": "Forrest Gump", "url": "https://www.imdb.com/title/tt0109830/"},
                    {"title": "Cast Away", "year": "2000", "role": "Chuck Noland", "url": "https://www.imdb.com/title/tt0162222/"}
                ],
                "known_for": [
                    {"title": "Forrest Gump", "year": "1994", "url": "https://www.imdb.com/title/tt0109830/"},
                    {"title": "Saving Private Ryan", "year": "1998", "url": "https://www.imdb.com/title/tt0120815/"}
                ]
            }
        }

# Cache for actor details
actor_details_cache = {}

# Helper functions
def normalize_imdb_id(imdb_id: str) -> str:
    """
    Ensure the IMDb ID has the 'tt' prefix.
    
    Args:
        imdb_id: The IMDb ID to normalize
        
    Returns:
        Normalized IMDb ID with 'tt' prefix
    """
    return f"tt{imdb_id}" if not imdb_id.startswith('tt') else imdb_id

def normalize_person_id(person_id: str) -> str:
    """
    Ensure the IMDb person ID has the 'nm' prefix.
    
    Args:
        person_id: The IMDb person ID to normalize
        
    Returns:
        Normalized IMDb person ID with 'nm' prefix
    """
    return f"nm{person_id}" if not person_id.startswith('nm') else person_id

@lru_cache(maxsize=100)
def get_imdb_url(imdb_id: str) -> str:
    """
    Get the IMDB URL for a movie ID.
    
    Args:
        imdb_id: IMDB ID (with or without 'tt' prefix)
        
    Returns:
        Full IMDB URL
    """
    return f"https://www.imdb.com/title/{normalize_imdb_id(imdb_id)}/"

@lru_cache(maxsize=100)
def get_person_url(person_id: str) -> str:
    """
    Get the IMDB URL for a person ID.
    
    Args:
        person_id: IMDB person ID (with or without 'nm' prefix)
        
    Returns:
        Full IMDB URL
    """
    return f"https://www.imdb.com/name/{normalize_person_id(person_id)}/"

async def search_imdb(
    query: str, 
    content_type: Optional[str] = None,
    limit: int = 5
) -> SearchResponse:
    """
    Search IMDB for movies, TV shows, or other content using Cinemagoer.
    
    Args:
        query: Search query
        content_type: Type of content to search for ('movie', 'tv', 'person')
        limit: Maximum number of results to return (default: 10)
        
    Returns:
        SearchResponse object with results
        
    Raises:
        ValueError: If an invalid content_type is provided
        RuntimeError: If the IMDb search fails
    """
    logger.info(f"Searching IMDB for: {query} (type: {content_type or 'movie'})")
    
    # Map content types to search methods
    search_methods = {
        "person": ia.search_person,
        "tv": ia.search_movie,  # Use search_movie for TV shows too
        "movie": ia.search_movie,
        None: ia.search_movie  # Default to movie search
    }
    
    # Get the appropriate search method
    search_method = search_methods.get(content_type)
    if search_method is None and content_type is not None:
        valid_types = ", ".join(k for k in search_methods.keys() if k is not None)
        raise ValueError(f"Invalid content type: {content_type}. Valid types are: {valid_types}")
    
    try:
        # Run the search in a thread pool to avoid blocking
        loop = asyncio.get_running_loop()
        search_results = await loop.run_in_executor(None, search_method, query)
        
        results = []
        # Limit results to the specified number and filter by content type if needed
        count = 0
        for item in search_results:
            # Skip if we've reached the limit
            if count >= limit:
                break
                
            # For TV shows, only include items that are TV series or episodes
            if content_type == "tv":
                kind = item.get('kind', '')
                if kind not in ['tv series', 'tv mini series', 'tv movie', 'episode']:
                    continue
            # For movies, only include actual movies
            elif content_type == "movie":
                kind = item.get('kind', '')
                if kind in ['tv series', 'tv mini series', 'tv movie', 'episode']:
                    continue
            
            imdb_id = normalize_imdb_id(item.movieID)
            
            # Get year if available
            year = item.get('year')
            year_str = str(year) if year else None
            
            # Create result
            results.append(SearchResult(
                title=item.get('title', 'Unknown Title'),
                url=get_imdb_url(imdb_id),
                year=year_str,
                rating=None,  # Rating requires additional API call
                description=None,  # Description requires additional API call
                imdb_id=imdb_id
            ))
            count += 1
        
        return SearchResponse(
            results=results,
            total_results=len(search_results)
        )
    except Exception as e:
        logger.error(f"Error searching IMDb: {str(e)}")
        raise RuntimeError(f"Failed to search IMDb: {str(e)}")

async def fetch_movie_details(movie_id: str) -> MovieDetails:
    """
    Fetch movie details from IMDB using Cinemagoer.
    This function does the actual work of fetching the data.
    
    Args:
        movie_id: IMDB movie ID (with or without 'tt' prefix)
        
    Returns:
        MovieDetails object with movie information
        
    Raises:
        RuntimeError: If fetching movie details fails
    """
    logger.info(f"Fetching details for movie ID: {movie_id}")
    
    # Normalize ID first, then strip 'tt' prefix as Cinemagoer requires numeric ID
    normalized_id = normalize_imdb_id(movie_id)
    numeric_id = normalized_id[2:]  # Strip 'tt' prefix
    
    try:
        # Run the API call in a thread pool to avoid blocking
        loop = asyncio.get_running_loop()
        
        # Get movie details with specific information sets
        movie = await loop.run_in_executor(
            None, 
            #lambda: ia.get_movie(numeric_id, ['main', 'plot', 'cast'])
            lambda: ia.get_movie(numeric_id)
        )
        
        if not movie:
            raise ValueError(f"Movie with ID {movie_id} not found")
        
        # Extract director(s)
        directors = []
        if 'director' in movie:
            directors_data = movie.get('director', [])
            if isinstance(directors_data, list):
                directors = [director.get('name') for director in directors_data]
            else:
                 directors = [directors_data.get('name')]
        
        # Extract cast
        cast = []
        if 'cast' in movie:
            cast = [actor.get('name') for actor in movie.get('cast', [])[:5]]  # Limit to first 5 cast members
        
        # Extract plot
        plot = None
        if 'plot' in movie and movie['plot']:
            plot = movie['plot'][0].split('::')[0].strip()  # Get first plot and remove author info
        
        # Extract runtime
        runtime = None
        if 'runtimes' in movie and movie['runtimes']:
            runtime = f"{movie['runtimes'][0]} min"
        
        # Create MovieDetails object
        return MovieDetails(
            title=movie.get('title', 'Unknown Title'),
            year=str(movie.get('year')) if movie.get('year') else None,
            rating=str(movie.get('rating')) if movie.get('rating') else None,
            genres=movie.get('genres', []),
            director=directors[0] if directors else None,
            cast=cast,
            plot=plot,
            poster_url=movie.get('cover url') if 'cover url' in movie else None,
            runtime=runtime,
            imdb_id=normalized_id
        )
    except Exception as e:
        logger.error(f"Error fetching movie details: {str(e)}")
        raise RuntimeError(f"Failed to fetch movie details for {movie_id}: {str(e)}")

async def get_movie_details(movie_id: str) -> MovieDetails:
    """
    Get detailed information about a movie using Cinemagoer.
    This function handles caching of movie details.
    
    Args:
        movie_id: IMDB movie ID (with or without 'tt' prefix)
        
    Returns:
        MovieDetails object with movie information
        
    Raises:
        RuntimeError: If fetching movie details fails
    """
    # Normalize the ID for consistent caching
    normalized_id = normalize_imdb_id(movie_id)
    
    # Check if movie details are in cache
    if normalized_id in movie_details_cache:
        logger.info(f"Returning cached details for movie ID: {normalized_id}")
        return movie_details_cache[normalized_id]
    
    try:
        # Fetch movie details
        details = await fetch_movie_details(normalized_id)
        
        # Cache movie details (limit cache size to 100 entries)
        if len(movie_details_cache) >= 100:
            # Remove a random entry if cache is full
            movie_details_cache.pop(next(iter(movie_details_cache)))
        
        movie_details_cache[normalized_id] = details
        
        return details
    except Exception as e:
        # Pass through the exception from fetch_movie_details
        logger.error(f"Error in get_movie_details: {str(e)}")
        raise

# Cache for trending movies
trending_movies_cache = None
trending_movies_timestamp = 0

async def fetch_actor_details(person_id: str) -> ActorDetails:
    """
    Fetch actor/actress details from IMDB using Cinemagoer.
    This function does the actual work of fetching the data.
    
    Args:
        person_id: IMDB person ID (with or without 'nm' prefix)
        
    Returns:
        ActorDetails object with actor/actress information
        
    Raises:
        RuntimeError: If fetching actor details fails
    """
    logger.info(f"Fetching details for person ID: {person_id}")
    
    # Normalize ID first, then strip 'nm' prefix as Cinemagoer requires numeric ID
    normalized_id = normalize_person_id(person_id)
    numeric_id = normalized_id[2:]  # Strip 'nm' prefix
    
    try:
        # Run the API call in a thread pool to avoid blocking
        loop = asyncio.get_running_loop()
        
        # Get person details with specific information sets
        person = await loop.run_in_executor(
            None, 
            lambda: ia.get_person(numeric_id, info=['main', 'biography', 'filmography'])
        )
        
        if not person:
            raise ValueError(f"Person with ID {person_id} not found")
        
        # Extract filmography (limited to top roles)
        filmography = []
        known_for = []
        
        # Process filmography by categories (actor, director, etc.)
        for job_category in person.get('filmography', {}):
            # Get the job category name (actor, actress, director, etc.)
            category = job_category
            
            # Get the list of movies for this category
            movies = person.get('filmography', {}).get(category, [])
            
            # Add top movies to filmography (limit to 5 per category)
            for movie in movies[:5]:
                movie_id = movie.getID() if hasattr(movie, 'getID') else None
                imdb_url = get_imdb_url(f"tt{movie_id}") if movie_id else None
                
                film_entry = {
                    "title": movie.get('title', ''),
                    "year": str(movie.get('year', '')) if movie.get('year') else None,
                    "role": category,
                    "url": imdb_url
                }
                filmography.append(film_entry)
                
                # Add to known_for if it's an acting role (limit to 3 total)
                if category in ['actor', 'actress'] and len(known_for) < 3:
                    known_for.append({
                        "title": movie.get('title', ''),
                        "year": str(movie.get('year', '')) if movie.get('year') else None,
                        "url": imdb_url
                    })
        
        # Extract biography
        bio = None
        if 'biography' in person and person['biography']:
            # Get the first paragraph of the biography
            bio_text = person.get('biography', '')
            if bio_text:
                # Take first paragraph or limit to 500 chars
                bio = bio_text.split('\n\n')[0][:500]
                if len(bio_text) > 500:
                    bio += "..."
        
        # Create ActorDetails object
        return ActorDetails(
            name=person.get('name', 'Unknown Name'),
            imdb_id=normalized_id,
            url=get_person_url(normalized_id),
            birth_date=person.get('birth date'),
            birth_place=person.get('birth place'),
            death_date=person.get('death date'),
            biography=bio,
            photo_url=person.get('headshot'),
            height=person.get('height'),
            filmography=filmography,
            known_for=known_for
        )
    except Exception as e:
        logger.error(f"Error fetching actor details: {str(e)}")
        raise RuntimeError(f"Failed to fetch actor details for {person_id}: {str(e)}")

async def get_actor_details(person_id: str) -> ActorDetails:
    """
    Get detailed information about an actor/actress using Cinemagoer.
    This function handles caching of actor details.
    
    Args:
        person_id: IMDB person ID (with or without 'nm' prefix)
        
    Returns:
        ActorDetails object with actor/actress information
        
    Raises:
        RuntimeError: If fetching actor details fails
    """
    # Normalize the ID for consistent caching
    normalized_id = normalize_person_id(person_id)
    
    # Check if actor details are in cache
    if normalized_id in actor_details_cache:
        logger.info(f"Returning cached details for person ID: {normalized_id}")
        return actor_details_cache[normalized_id]
    
    try:
        # Fetch actor details
        details = await fetch_actor_details(normalized_id)
        
        # Cache actor details (limit cache size to 100 entries)
        if len(actor_details_cache) >= 100:
            # Remove a random entry if cache is full
            actor_details_cache.pop(next(iter(actor_details_cache)))
        
        actor_details_cache[normalized_id] = details
        
        return details
    except Exception as e:
        # Pass through the exception from fetch_actor_details
        logger.error(f"Error in get_actor_details: {str(e)}")
        raise

class PersonSearchResult(BaseModel):
    """
    Model for person search results from IMDB.
    """
    name: str
    imdb_id: str
    url: str
    known_for: List[str] = []
    
    class Config:
        """Configuration for Pydantic model."""
        json_encoders = {
            # Custom encoders if needed
        }
        json_schema_extra = {
            "example": {
                "name": "Tom Hanks",
                "imdb_id": "nm0000158",
                "url": "https://www.imdb.com/name/nm0000158/",
                "known_for": ["Forrest Gump", "Saving Private Ryan", "Cast Away"]
            }
        }

class PersonSearchResponse(BaseModel):
    """
    Model for person search response from IMDB.
    """
    results: List[PersonSearchResult]
    total_results: int
    
    class Config:
        """Configuration for Pydantic model."""
        json_encoders = {
            # Custom encoders if needed
        }
        json_schema_extra = {
            "example": {
                "results": [
                    {
                        "name": "Tom Hanks",
                        "imdb_id": "nm0000158",
                        "url": "https://www.imdb.com/name/nm0000158/",
                        "known_for": ["Forrest Gump", "Saving Private Ryan", "Cast Away"]
                    }
                ],
                "total_results": 1
            }
        }

async def search_people(query: str, limit: int = 10) -> PersonSearchResponse:
    """
    Search IMDB for actors, actresses, directors, and other people using Cinemagoer.
    
    Args:
        query: Search query
        limit: Maximum number of results to return (default: 10)
        
    Returns:
        PersonSearchResponse object with results
        
    Raises:
        RuntimeError: If the IMDb search fails
    """
    logger.info(f"Searching IMDB for people: {query}")
    
    try:
        # Run the search in a thread pool to avoid blocking
        loop = asyncio.get_running_loop()
        
        # Execute search for people
        search_results = await loop.run_in_executor(None, ia.search_person, query)
        
        results = []
        # Limit results to the specified number
        for person in search_results[:limit]:
            person_id = normalize_person_id(person.personID)
            
            # Extract known for titles if available
            known_for = []
            if 'known for' in person:
                known_for = [title for title in person.get('known for', [])[:3]]
            
            # Create result
            results.append(PersonSearchResult(
                name=person.get('name', 'Unknown Name'),
                imdb_id=person_id,
                url=get_person_url(person_id),
                known_for=known_for
            ))
        
        return PersonSearchResponse(
            results=results,
            total_results=len(search_results)
        )
    except Exception as e:
        logger.error(f"Error searching IMDb for people: {str(e)}")
        raise RuntimeError(f"Failed to search IMDb for people: {str(e)}")