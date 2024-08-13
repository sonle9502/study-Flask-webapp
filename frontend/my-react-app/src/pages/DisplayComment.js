import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { API_BASE_URL } from '../config';
import './DisplayComment.css'; // CSSファイルをインポート

const DisplayComment = ({ comment, onUpdate, onDelete }) => {
  const [isEditing, setIsEditing] = useState(false);
  const [editedContent, setEditedContent] = useState(comment.content);
  const inputRef = useRef(null);

  const handleEdit = () => {
    setIsEditing(true);
  };

  const handleSave = async () => {
    try {
      await axios.put(`${API_BASE_URL}/api/comments/${comment.id}`, { content: editedContent });
      setIsEditing(false);
      onUpdate(); // Re-fetch the task data or update the state
    } catch (error) {
      console.error('Error updating comment:', error);
    }
  };

  const handleCancel = () => {
    setIsEditing(false);
    setEditedContent(comment.content); // Reset to original content if editing is canceled
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      handleSave();
    }
  };

  const handleDelete = () => {
    const confirmed = window.confirm('Are you sure you want to delete this comment?');
    if (confirmed) {
      onDelete(comment.id);
    }
  };

  useEffect(() => {
    if (isEditing && inputRef.current) {
      inputRef.current.focus();
      inputRef.current.selectionStart = inputRef.current.value.length;
    }
  }, [isEditing]);

  return (
    <div key={comment.id} className="card comment-card">
      <div className="card-body">
        {isEditing ? (
          <div>
            <input
              type="text"
              className="form-control comment-content"
              value={editedContent}
              ref={inputRef}
              onChange={(e) => setEditedContent(e.target.value)}
              onKeyDown={handleKeyDown}  // Handle Enter key press
            />
            <div className="edit-buttons">
              <button onClick={handleSave} className="btn btn-success">Save</button>
              <button onClick={handleCancel} className="btn btn-secondary">Cancel</button>
            </div>
          </div>
        ) : (
          <div>
            <p className="card-text comment-content">{comment.content}</p>
              <footer className="blockquote-footer comment-timestamp">
                <span className="timestamp">{`${comment.created_at}`}</span>
              </footer>
            <div className="view-buttons">
              <button onClick={handleEdit} className="btn btn-secondary">Edit</button>
              <button onClick={handleDelete} className="btn btn-danger">Delete</button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default DisplayComment;
