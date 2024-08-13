import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { API_BASE_URL } from '../config';

const DisplayImage = ({ imageId, onDelete }) => {
  const [imageSrc, setImageSrc] = useState('');
  const [isModalOpen, setIsModalOpen] = useState(false);

  // Get CSRF token from meta tag
  const getCsrfToken = () => {
    const token = document.querySelector('meta[name="csrf-token"]').getAttribute('content');
    console.log('CSRF Token:', token); // Log the token for debugging
    return token;
  };

  useEffect(() => {
    if (!imageId) {
      console.error('No imageId provided');
      return;
    }

    const fetchImage = async () => {
      try {
        const response = await axios.get(`${API_BASE_URL}/image/${imageId}`, {
          responseType: 'blob' // Set response type to blob for binary data
        });
        const url = URL.createObjectURL(new Blob([response.data]));
        setImageSrc(url);
      } catch (error) {
        console.error('Error fetching image:', error);
      }
    };

    fetchImage();
  }, [imageId]);

  useEffect(() => {
    const handleKeyDown = (event) => {
      if (event.key === 'Escape' && isModalOpen) {
        setIsModalOpen(false);
      }
    };

    document.addEventListener('keydown', handleKeyDown);

    return () => {
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, [isModalOpen]);

  const handleDeleteImage = async () => {
    const confirmDelete = window.confirm('Are you sure you want to delete this image?');

    if (!confirmDelete) {
      return;
    }

    try {
      const response = await fetch(`${API_BASE_URL}/api/images/${imageId}`, {
        method: 'DELETE',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': getCsrfToken() // Ensure CSRF token is sent if required
        }
      });

      if (response.ok) {
        onDelete(); // Call the onDelete callback to refresh the tasks list
      } else {
        console.error('Failed to delete image:', response.statusText);
      }
    } catch (error) {
      console.error('Error deleting image:', error);
    }
  };

  const toggleModal = () => {
    setIsModalOpen(!isModalOpen);
  };

  return (
    <div style={{ position: 'relative', display: 'inline-block' }}>
      {imageSrc ? (
        <div>
          <img
            src={imageSrc}
            alt="Uploaded"
            onClick={toggleModal}
            style={{
              width: '130px', // Thumbnail size
              height: 'auto',
              cursor: 'pointer',
              paddingRight: '5px',
              borderRadius: '5px',
            }}
          />
          <button
            onClick={handleDeleteImage}
            style={{
              position: 'absolute',
              top: '5px',
              right: '5px',
              background: 'red',
              color: 'white',
              border: 'none',
              borderRadius: '50%',
              width: '25px',
              height: '25px',
              cursor: 'pointer',
              textAlign: 'center',
              lineHeight: '15px',  // Adjusted line height
              fontSize: '16px',
              justifyContent: 'center',
              paddingTop: '0px',
              paddingRight: '6px'
            }}
          >
            x
          </button>
        </div>
      ) : (
        'Loading...'
      )}

      {isModalOpen && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          width: '100%',
          height: '100%',
          backgroundColor: 'rgba(0, 0, 0, 0.8)',
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          zIndex: 1000,
        }} onClick={toggleModal}>
          <img
            src={imageSrc}
            alt="Enlarged"
            style={{
              maxWidth: '90%',
              maxHeight: '90%',
            }}
          />
        </div>
      )}
    </div>
  );
};

export default DisplayImage;