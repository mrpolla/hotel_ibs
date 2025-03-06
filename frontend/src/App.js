import React, { useState } from "react";
import "./App.css";

function App() {
  // State to store the search query, images returned for that query, and loading message.
  const [query, setQuery] = useState("");
  const [filteredImages, setFilteredImages] = useState([]);
  const [selectedImages, setSelectedImages] = useState([]);
  const [loadingMessage, setLoadingMessage] = useState("");

  // Check if a pre-signed URL is expired.
  const isUrlExpired = (url) => {
    const match = url.match(/X-Amz-Expires=(\d+)/);
    if (!match) return true;

    const expiresInSeconds = parseInt(match[1], 10);
    const creationTime = Date.now() - expiresInSeconds * 1000;
    return Date.now() > creationTime;
  };

  // Fetch a new pre-signed URL for a specific image.
  const fetchNewUrl = async (imageId) => {
    try {
      const response = await fetch(
        `http://localhost:5000/api/image/${imageId}`
      );
      const updatedImage = await response.json();
      return updatedImage.image_url;
    } catch (error) {
      console.error(`Error fetching new URL for image ${imageId}:`, error);
      return null;
    }
  };

  // Download an image and convert it into an object URL.
  const downloadImageUrl = async (url) => {
    try {
      const response = await fetch(url);
      const blob = await response.blob();
      return URL.createObjectURL(blob);
    } catch (error) {
      console.error("Error downloading image:", error);
      return null;
    }
  };

  // Fetch images from the backend based on the search query.
  const fetchImagesByTag = async (tag) => {
    const response = await fetch(
      `http://localhost:5000/api/images?tag=${encodeURIComponent(tag)}`
    );
    const data = await response.json();
    return data;
  };

  // Update images with expired pre-signed URLs.
  const updateExpiredUrls = async (images) => {
    return await Promise.all(
      images.map(async (image) => {
        if (!image.image_url || isUrlExpired(image.image_url)) {
          const newUrl = await fetchNewUrl(image.id);
          return newUrl ? { ...image, image_url: newUrl } : image;
        }
        return image;
      })
    );
  };

  // Download images and attach object URLs for display.
  const downloadImages = async (images) => {
    const updatedImages = [];
    for (let index = 0; index < images.length; index++) {
      const image = images[index];
      const downloaded_url = await downloadImageUrl(image.image_url);
      updatedImages.push(downloaded_url ? { ...image, downloaded_url } : image);
      updateLoadingBar(10 + ((index + 1) / images.length) * 90); // Update loading bar based on progress
      setLoadingMessage(
        `Found ${images.length} results, downloading image ${
          index + 1
        } out of ${images.length}...`
      );
    }
    return updatedImages;
  };

  // Handle search operation: fetch images, update URLs, download images, and update state.
  const handleSearch = async () => {
    if (query.trim() === "") return; // Do nothing if query is empty.
    console.log("Searching for images with tag:", query);

    try {
      // Step 1: Fetch images based on the queried tag.
      setLoadingMessage("Searching database...");
      updateLoadingBar(10); // Update loading bar to 10%
      const imagesByTag = await fetchImagesByTag(query);
      console.log("Images fetched for query:", imagesByTag);
      setLoadingMessage(
        `Found ${imagesByTag.length} results, downloading images...`
      );

      // Step 2: Update expired pre-signed URLs if needed.
      const imagesWithUpdatedUrls = await updateExpiredUrls(imagesByTag);

      // Step 3: Download images to generate object URLs.
      const finalImages = await downloadImages(imagesWithUpdatedUrls);

      // Step 4: Update state with the processed images.
      setLoadingMessage("Displaying images...");
      updateLoadingBar(100); // Update loading bar to 100%
      setFilteredImages(finalImages);
      setLoadingMessage("Done");
    } catch (error) {
      console.error("Error fetching images for query:", error);
      updateLoadingBar(0); // Reset loading bar on error
      setLoadingMessage("Error occurred");
    }
  };

  // Add this JavaScript to handle the loading bar progress
  function updateLoadingBar(progress) {
    const loadingBarProgress = document.getElementById("loadingBarProgress");
    loadingBarProgress.style.width = progress + "%";
  }

  // Handle double-click event to move images between containers
  const handleImageDoubleClick = (image, fromSelected) => {
    if (fromSelected) {
      setSelectedImages(selectedImages.filter((img) => img !== image));
      setFilteredImages([...filteredImages, image]);
    } else {
      setFilteredImages(filteredImages.filter((img) => img !== image));
      setSelectedImages([...selectedImages, image]);
    }
  };

  return (
    <div className="container">
      <h1 className="title">Image Based Hotel Search</h1>
      <input
        type="text"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        onKeyDown={(e) => e.key === "Enter" && handleSearch()}
        placeholder="Enter image tag"
        className="input"
      />
      <button onClick={handleSearch} className="button">
        Search
      </button>
      <div className="loading-bar">
        <div className="loading-bar-progress" id="loadingBarProgress"></div>
      </div>
      <div className="loading-message">{loadingMessage}</div>
      <div className="image-container-wrapper">
        <div className="image-container-sub-wrapper">
          <div className="image-container-label">Tagged images</div>
          <div className="image-container">
            {filteredImages.map((image, index) => (
              <img
                key={index}
                src={image.downloaded_url || image.image_url}
                alt={image.tags.map((tag) => tag.tag_name).join(", ")}
                className="image"
                onDoubleClick={() => handleImageDoubleClick(image, false)}
              />
            ))}
          </div>
        </div>
        <div className="image-container-sub-wrapper">
          <div className="image-container-label">Selected images</div>
          <div className="image-container right">
            {selectedImages.map((image, index) => (
              <img
                key={index}
                src={image.downloaded_url || image.image_url}
                alt={image.tags.map((tag) => tag.tag_name).join(", ")}
                className="image"
                onDoubleClick={() => handleImageDoubleClick(image, true)}
              />
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;
