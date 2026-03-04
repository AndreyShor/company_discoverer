import React, { useState } from 'react';
import './Sidebar.css';

const Sidebar = ({ activeTab, setActiveTab }) => {
  return (
    <div className="sidebar">
      <div className="sidebar-header">
        <h2>Andrey's Hub</h2>
      </div>
      <nav className="sidebar-nav">
        <button 
          className={`nav-btn ${activeTab === 'showcase' ? 'active' : ''}`}
          onClick={() => setActiveTab('showcase')}
        >
          Personal Showcase
        </button>
        <button 
          className={`nav-btn ${activeTab === 'experiment' ? 'active' : ''}`}
          onClick={() => setActiveTab('experiment')}
        >
          RAG vs HyDE Experiment
        </button>
      </nav>
      <div className="sidebar-footer">
        <p>Gemma 1B / 4B</p>
      </div>
    </div>
  );
};

export default Sidebar;
