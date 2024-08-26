import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import CreateTask from './pagescomponent/CreateTask';
import HomePage from './pagescomponent/HomePage';
import TaskDetail from './pagescomponent/TaskDetail';  
import Handwritten from './pages/Handwritten';
import Kanjiwriten from './pages/Kanjiwriten';

function App() {
  return (
    <Router>
      <div className="App">
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/search" element={<HomePage />} />
          <Route path="/create-task" element={<CreateTask />} />
          <Route path="/task/:taskId" element={<TaskDetail />} /> 
          <Route path="/handwritten" element={<Handwritten />} /> 
          <Route path="/kanjihandwriting" element={<Kanjiwriten />} /> 
          {/* 他のルートをここに追加 */}
        </Routes>
      </div>
    </Router>
  );
}

export default App;
