# app/routes/books.py
from fastapi import APIRouter, HTTPException
import requests
import re
import traceback
from typing import List, Dict

router = APIRouter()

@router.get("/search-and-read")
async def search_and_read_book(query: str):
    """Search for books and get content from Project Gutenberg"""
    try:
        print(f"🔍 Search and read: '{query}'")
        
        
        search_results = await search_gutenberg(query)
        
        if not search_results:
            raise HTTPException(status_code=404, detail="No books found for this query")
        
       
        book_info = search_results[0]
        print(f"📖 Selected book: {book_info['title']} by {book_info['author']}")
        
        
        content = await fetch_gutenberg_content(book_info['id'])
        
        if not content:
            raise HTTPException(status_code=404, detail="Book content not available")
        
        
        cleaned_content = clean_gutenberg_content(content)
        
        
        word_count = len(cleaned_content.split())
        estimated_pages = max(1, word_count // 250)  
        
        print(f"📊 Content stats: {len(cleaned_content)} chars, {word_count} words, ~{estimated_pages} pages")
        
        
        return {
            "search_query": query,
            "book": {
                "id": book_info['id'],
                "title": book_info['title'],
                "author": book_info['author'],
                "language": book_info.get('language', 'en'),
                "bookshelf": book_info.get('bookshelf', []),
                "downloads": book_info.get('downloads', 0)
            },
            "content": cleaned_content,
            "total_chars": len(cleaned_content),
            "word_count": word_count,
            "estimated_pages": estimated_pages,
            "source": "Project Gutenberg",
            "note": "Full text content provided"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error in search-and-read: {e}")
        print(f"💥 Full traceback:\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail="Failed to get book content")

async def search_gutenberg(query: str, max_results: int = 10) -> List[Dict]:
    """Search Project Gutenberg for books"""
    try:
        print(f"🌐 Searching Project Gutenberg for: '{query}'")
        
        
        search_url = "https://gutendex.com/books/"
        params = {
            'search': query,
            'languages': 'en',  
        }
        
        response = requests.get(search_url, params=params, timeout=30)
        
        if response.status_code != 200:
            print(f"❌ Gutenberg search failed: {response.status_code}")
            return []
        
        data = response.json()
        books = data.get('results', [])
        
        print(f"📚 Found {len(books)} books on Project Gutenberg")
        
       
        formatted_books = []
        for book in books[:max_results]:
            authors = [author['name'] for author in book.get('authors', [])]
            author_name = authors[0] if authors else "Unknown Author"
            
            formatted_books.append({
                'id': book['id'],
                'title': book.get('title', 'Unknown Title'),
                'author': author_name,
                'language': book.get('languages', ['en'])[0],
                'bookshelf': book.get('bookshelf', []),
                'downloads': book.get('download_count', 0),
                'subjects': book.get('subjects', []),
                'media_type': book.get('media_type', '')
            })
        
        return formatted_books
        
    except Exception as e:
        print(f"❌ Gutenberg search error: {e}")
        return []

async def fetch_gutenberg_content(book_id: int) -> str:
    """Fetch book content from Project Gutenberg"""
    try:
        print(f"📖 Fetching Gutenberg content for book ID: {book_id}")
        
        
        mirrors = [
            f"https://www.gutenberg.org/cache/epub/{book_id}/pg{book_id}.txt",
            f"https://www.gutenberg.org/files/{book_id}/{book_id}-0.txt",
            f"https://www.gutenberg.org/files/{book_id}/{book_id}.txt",
            f"https://www.gutenberg.org/ebooks/{book_id}.txt.utf-8",
        ]
        
        for mirror_url in mirrors:
            print(f"🔗 Trying mirror: {mirror_url}")
            try:
                response = requests.get(mirror_url, timeout=30)
                if response.status_code == 200:
                    content_length = len(response.text)
                    print(f"✅ Successfully fetched {content_length:,} characters from {mirror_url}")
                    return response.text
            except Exception as e:
                print(f"❌ Mirror failed: {e}")
                continue
        
        print("❌ All mirrors failed")
        return ""
        
    except Exception as e:
        print(f"❌ Gutenberg content fetch error: {e}")
        return ""

def clean_gutenberg_content(content: str) -> str:
    """Clean Project Gutenberg content"""
    try:
        if not content:
            return ""
            
        
        lines = content.split('\n')
        
        
        start_index = 0
        header_patterns = [
            "START OF THIS PROJECT GUTENBERG EBOOK",
            "START OF THE PROJECT GUTENBERG EBOOK", 
            "*** START OF THIS PROJECT GUTENBERG EBOOK",
            "*** START OF THE PROJECT GUTENBERG EBOOK"
        ]
        
        for i, line in enumerate(lines):
            if any(pattern in line.upper() for pattern in header_patterns):
                start_index = i + 1
                print(f"📖 Found content start at line {i}")
                break
        
        
        end_index = len(lines)
        footer_patterns = [
            "END OF THIS PROJECT GUTENBERG EBOOK",
            "END OF THE PROJECT GUTENBERG EBOOK",
            "*** END OF THIS PROJECT GUTENBERG EBOOK",
            "*** END OF THE PROJECT GUTENBERG EBOOK"
        ]
        
        for i, line in enumerate(lines):
            if any(pattern in line.upper() for pattern in footer_patterns):
                end_index = i
                print(f"📖 Found content end at line {i}")
                break
        
        
        if start_index > 0 and end_index > start_index:
            content = '\n'.join(lines[start_index:end_index])
            print(f"📖 Extracted content: {len(content):,} characters")
        else:
            print("📖 Using full content (no headers/footers found)")
        
        
        content = re.sub(r'\n\s*\n', '\n\n', content)
        content = re.sub(r'[ \t]+\n', '\n', content)
        
        final_length = len(content)
        print(f"📖 Final cleaned content: {final_length:,} characters")
        
        return content.strip()
        
    except Exception as e:
        print(f"❌ Content cleaning error: {e}")
        return content

@router.get("/test-gutenberg-search")
async def test_gutenberg_search(query: str = "sherlock holmes"):
    """Test Project Gutenberg search"""
    try:
        results = await search_gutenberg(query, max_results=5)
        
        
        if results:
            first_book = results[0]
            content = await fetch_gutenberg_content(first_book['id'])
            content_available = bool(content)
            first_book['content_available'] = content_available
            
            if content_available:
                cleaned_content = clean_gutenberg_content(content)
                first_book['content_length'] = len(cleaned_content)
                first_book['word_count'] = len(cleaned_content.split())
                first_book['estimated_pages'] = max(1, first_book['word_count'] // 250)
        
        return {
            "query": query,
            "results": results,
            "total_found": len(results)
        }
        
    except Exception as e:
        return {"error": str(e)}

@router.get("/test-gutenberg-book/{book_id}")
async def test_gutenberg_book(book_id: int):
    """Test specific Project Gutenberg book"""
    try:
        
        info_url = f"https://gutendex.com/books/{book_id}"
        response = requests.get(info_url)
        
        if response.status_code != 200:
            return {"error": "Book not found"}
        
        book_info = response.json()
        
        
        content = await fetch_gutenberg_content(book_id)
        content_available = bool(content)
        
        if content_available:
            cleaned_content = clean_gutenberg_content(content)
            content_preview = cleaned_content[:500] + "..." if len(cleaned_content) > 500 else cleaned_content
            word_count = len(cleaned_content.split())
            estimated_pages = max(1, word_count // 250)
        else:
            content_preview = "Content not available"
            word_count = 0
            estimated_pages = 0
        
        return {
            "book_info": book_info,
            "content_available": content_available,
            "content_preview": content_preview,
            "content_length": len(content) if content else 0,
            "word_count": word_count,
            "estimated_pages": estimated_pages
        }
        
    except Exception as e:
        return {"error": str(e)}

@router.get("/popular-books")
async def get_popular_books():
    """Get popular Project Gutenberg books"""
    try:
        url = "https://gutendex.com/books/?sort=popular"
        response = requests.get(url)
        
        if response.status_code == 200:
            data = response.json()
            books = data.get('results', [])[:10]  
            for book in books:
                content = await fetch_gutenberg_content(book['id'])
                book['content_available'] = bool(content)
                if content:
                    cleaned_content = clean_gutenberg_content(content)
                    book['content_length'] = len(cleaned_content)
                    book['word_count'] = len(cleaned_content.split())
                    book['estimated_pages'] = max(1, book['word_count'] // 250)
            
            return {
                "popular_books": books,
                "source": "Project Gutenberg"
            }
        else:
            return {"error": "Failed to fetch popular books"}
            
    except Exception as e:
        return {"error": str(e)}

@router.get("/test")
async def test_endpoint():
    """Test endpoint"""
    return {
        "message": "Books API with Project Gutenberg integration",
        "status": "success"
    }