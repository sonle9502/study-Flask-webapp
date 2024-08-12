import React, { useState, useRef } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';

const URL = "http://127.0.0.1:5000";

const UploadImages = ({ taskId ,onUploadSuccess}) => {
  const [files, setFiles] = useState([]);
  const navigate = useNavigate();
  const fileInputRef = useRef(null); // Create a ref for the file input

  // Get CSRF token from meta tag
  const getCsrfToken = () => {
    const token = document.querySelector('meta[name="csrf-token"]').getAttribute('content');
    console.log('CSRF Token:', token); // Log the token for debugging
    return token;
  };

  const handleFileChange = (event) => {
    setFiles(event.target.files);
  };

  const handleSubmit = async (event) => {
    event.preventDefault();

    if (!taskId) {
      console.error('No task ID provided');
      return;
    }

    const formData = new FormData();
    for (let i = 0; i < files.length; i++) {
      formData.append('files', files[i]);
    }

    try {
      const response = await axios.post(`${URL}/upload_images/${taskId}`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
          'X-CSRFToken': getCsrfToken(), // Call the function to get the CSRF token
        }
      });
      console.log('Files uploaded successfully:', response.data);
      fileInputRef.current.value = ''; // Clear the file input
      setFiles([]); // Reset the files state
      navigate('/'); // Navigate to /data route on success
      onUploadSuccess(); // Trigger the callback to refresh data
    } catch (error) {
      console.error('Error uploading files:', error);
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      <input type="file" multiple onChange={handleFileChange} ref={fileInputRef} /> {/* Attach the ref to the input */}
      <button type="submit">Upload</button>
    </form>
  );
};

export default UploadImages;
