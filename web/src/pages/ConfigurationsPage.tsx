/**
 * Configurations page for managing personality configurations
 */

import React from 'react';
import PersonalityManagementDashboard from '../components/PersonalityManagementDashboard';
import './ConfigurationsPage.css';

const ConfigurationsPage: React.FC = () => {
  return (
    <div className="configurations-page">
      <PersonalityManagementDashboard />
    </div>
  );
};

export default ConfigurationsPage;