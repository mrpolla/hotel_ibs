import React, { useState, useEffect } from 'react';
import './App.css';

function App() {
  const [query, setQuery] = useState('');
  const [images, setImages] = useState([]);
  const [filteredImages, setFilteredImages] = useState([]);

  useEffect(() => {
    const cachedImageIds = localStorage.getItem('imageIds');
    
    if (cachedImageIds) {
      const parsedImageIds = JSON.parse(cachedImageIds);
      fetchImagesByIds(parsedImageIds);
    } else {
      fetchAllImages();
    }
  }, []);

  const fetchAllImages = async () => {
    try {
      const response = await fetch('http://localhost:5000/api/images');
      const data = await response.json();
      console.log('Fetched images:', data);

      // Store only image IDs in localStorage
      const imageIds = data.map(img => img.id);
      localStorage.setItem('imageIds', JSON.stringify(imageIds));

      setImages(data);
    } catch (error) {
      console.error('Error fetching images:', error);
    }
  };

  const fetchImagesByIds = async (imageIds) => {
    try {
      const response = await fetch(`http://localhost:5000/api/images?ids=${imageIds.join(',')}`);
      const data = await response.json();
      setImages(data);
    } catch (error) {
      console.error('Error fetching images by IDs:', error);
    }
  };

  const isExpired = (url) => {
    const match = url.match(/X-Amz-Expires=(\d+)/);
    if (!match) return true;

    const expiresInSeconds = parseInt(match[1], 10);
    const creationTime = new Date().getTime() - expiresInSeconds * 1000;

    return new Date().getTime() > creationTime;
  };

  const handleSearch = async () => {
    console.log('Search query:', query);
    
    const filtered = images.filter(image => 
      image.tags.some(tag => tag.tag_name.toLowerCase().includes(query.toLowerCase()))
    );

    console.log('Filtered images:', filtered);

    const updatedImages = await Promise.all(filtered.map(async (image) => {
      if (!image.image_url || isExpired(image.image_url)) {
        // Fetch new pre-signed URL for the image
        try {
          const response = await fetch(`http://localhost:5000/api/image/${image.id}`);
          const updatedImage = await response.json();
          return { ...image, image_url: updatedImage.image_url };
        } catch (error) {
          console.error(`Error fetching new URL for image ${image.id}`, error);
          return image; // Return old image in case of an error
        }
      }
      return image;
    }));

    // Download images and create object URLs
    const downloadedImages = await Promise.all(
      updatedImages.map(async (image) => {
        try {
          const response = await fetch(image.image_url);
          const blob = await response.blob();
          const url = URL.createObjectURL(blob);
          return { ...image, downloaded_url: url };
        } catch (error) {
          console.error(`Error downloading image ${image.id}`, error);
          return image;
        }
      })
    );

    setFilteredImages(downloadedImages);
  };

  return (
    <div className="container">
      <h1 className="title">Search Application</h1>
      <input
        type="text"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder="Enter image tag"
        className="input"
      />
      <button onClick={handleSearch} className="button">
        Search
      </button>
      <div className="image-container">
        {filteredImages.map((image, index) => (
          <img key={index} src={image.downloaded_url || image.image_url} alt={image.tags.map(tag => tag.tag_name).join(', ')} className="image" />
        ))}
      </div>
    </div>
  );
}

export default App;
