import React, { useState, useEffect } from 'react';
import './CreateTask.css'; // CSSファイルをインポート

function CreateTask() {
  const [content, setContent] = useState('');
  const [description, setDescription] = useState('');
  const [dueDate, setDueDate] = useState('');
  const [csrfToken, setCsrfToken] = useState('');

  useEffect(() => {
    fetch('/get-csrf-token', {
      credentials: 'include' // クッキー情報を含めてリクエストを送信
    })
      .then(response => {
        if (!response.ok) {
          throw new Error('Failed to fetch CSRF token');
        }
        return response.json();
      })
      .then(data => {
        setCsrfToken(data.csrf_token);
        console.log('CSRF Token:', data.csrf_token); // デバッグ用にCSRFトークンを表示
      })
      .catch(error => console.error('Error fetching CSRF token:', error));
  }, []);

  const formatDateForBackend = (dateStr) => {
    const date = new Date(dateStr);
    if (isNaN(date.getTime())) {
      console.error('Invalid Date:', dateStr); // デバッグ用
      return '';
    }
    return date.toISOString(); // ISO 8601形式に変換
  };

  const handleSubmit = (event) => {
    event.preventDefault();
    const formattedDueDate = formatDateForBackend(dueDate);
    const taskData = {
      content,
      description,
      dueDate: formattedDueDate
    };
    console.log("Sending task data:", taskData);  // デバッグ情報の追加

    fetch('/add', {
      method: 'POST',
      credentials: 'include', // クッキー情報を含めてリクエストを送信
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': csrfToken // CSRFトークンをヘッダーに追加
      },
      body: JSON.stringify(taskData),
    })
    .then(response => {
      if (response.ok) {
        return response.json();
      } else {
        return response.text().then(text => { throw new Error(text) });
      }
    })
    .then(data => {
      console.log('Task created:', data);
      window.location.href = '/';
    })
    .catch((error) => {
      console.error('Error:', error);
    });
  };

  return (
    <div>
      <h1>Create Task</h1>
      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label htmlFor="content">Content</label>
          <input
            type="text"
            className="form-control"
            id="content"
            value={content}
            onChange={(e) => setContent(e.target.value)}
            required
          />
        </div>
        <div className="form-group">
          <label htmlFor="description">Description</label>
          <textarea
            className="form-control"
            id="description"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            required
          ></textarea>
        </div>
        <div className="form-group">
          <label htmlFor="dueDate">Due Date</label>
          <input
            type="datetime-local"
            className="form-control"
            id="dueDate"
            value={dueDate}
            onChange={(e) => setDueDate(e.target.value)}
            required
          />
        </div>
        <button type="submit" className="btn btn-primary">
          Create Task
        </button>
      </form>
    </div>
  );
}

export default CreateTask;
