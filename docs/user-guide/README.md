# User Guide

Welcome to the Covibe User Guide! This comprehensive guide will help you get the most out of the Agent Personality System.

## Table of Contents

1. [Getting Started](#getting-started)
2. [Creating Personalities](#creating-personalities)
3. [Managing Personalities](#managing-personalities)
4. [IDE Integration](#ide-integration)
5. [Chat Interface](#chat-interface)
6. [Advanced Features](#advanced-features)
7. [Best Practices](#best-practices)
8. [Troubleshooting](#troubleshooting)

## Getting Started

### What is Covibe?

Covibe is an Agent Personality System that enhances your coding experience by adding configurable personality traits to your AI coding assistants. Instead of generic responses, your coding agent can respond like Tony Stark, Yoda, or any personality you choose.

### How It Works

1. **Describe a Personality**: Tell Covibe what personality you want (e.g., "Tony Stark")
2. **Automatic Research**: Covibe researches the personality from multiple sources
3. **Context Generation**: Creates appropriate prompts for your coding agent
4. **IDE Integration**: Automatically configures your IDE with the personality
5. **Enhanced Coding**: Your agent now responds with the chosen personality

### Key Benefits

- **Personalized Experience**: Make coding more engaging and fun
- **Consistent Personality**: Maintain character traits across all interactions
- **Multiple Personalities**: Switch between different personalities for different projects
- **Easy Integration**: Works with popular IDEs out of the box
- **Flexible Input**: Use web interface, API, or chat to configure personalities

## Creating Personalities

### Using the Web Interface

1. **Open Covibe** in your browser (`http://localhost:8000`)
2. **Enter Personality Description**:
   - Celebrity: "Albert Einstein"
   - Fictional Character: "Sherlock Holmes"
   - Archetype: "Patient mentor"
   - Combination: "Tony Stark but more patient"
3. **Select Project Directory**: Choose your coding project folder
4. **Generate Configuration**: Click "Generate" and wait for research
5. **Review Results**: Check the generated personality profile
6. **Apply to IDE**: Confirm to write configuration files

### Using the API

```bash
# Create a personality configuration
curl -X POST http://localhost:8000/api/personality \
  -H "Content-Type: application/json" \
  -d '{
    "description": "Tony Stark from Iron Man",
    "project_path": "/path/to/your/project",
    "user_id": "your_user_id"
  }'
```

### Using the Chat Interface

1. **Open Chat Tab** in the web interface
2. **Type Natural Language**:
   - "I want my agent to be like Tony Stark"
   - "Make it sound more like Yoda"
   - "Switch to a patient teacher personality"
3. **Refine Through Conversation**:
   - "Make it less sarcastic"
   - "Add more technical explanations"
   - "Keep the wit but be more encouraging"

### Personality Types

#### Celebrities and Historical Figures
- **Scientists**: Einstein, Tesla, Curie, Hawking
- **Tech Leaders**: Jobs, Gates, Musk, Torvalds
- **Authors**: Hemingway, Tolkien, Asimov
- **Philosophers**: Socrates, Nietzsche, Confucius

#### Fictional Characters
- **Sci-Fi**: Spock, Data, HAL 9000, Jarvis
- **Fantasy**: Gandalf, Yoda, Dumbledore
- **Literature**: Sherlock Holmes, Atticus Finch
- **Movies/TV**: Tony Stark, House MD, Tyrion Lannister

#### Character Archetypes
- **Mentor**: Patient, encouraging, educational
- **Expert**: Authoritative, precise, comprehensive
- **Friend**: Casual, supportive, relatable
- **Coach**: Motivating, challenging, results-focused
- **Scholar**: Academic, thorough, analytical

### Research Process

When you create a personality, Covibe:

1. **Analyzes Input**: Determines personality type and key traits
2. **Searches Sources**: Wikipedia, character databases, curated knowledge
3. **Extracts Traits**: Communication style, mannerisms, speech patterns
4. **Generates Context**: Creates LLM-compatible personality prompts
5. **Validates Results**: Ensures accuracy and consistency

## Managing Personalities

### Viewing Configurations

```bash
# List all personalities
curl http://localhost:8000/api/personality/configs

# Get specific personality
curl http://localhost:8000/api/personality/{personality_id}
```

### Updating Personalities

```bash
# Update personality description
curl -X PUT http://localhost:8000/api/personality/{personality_id} \
  -H "Content-Type: application/json" \
  -d '{
    "description": "Tony Stark but more patient",
    "project_path": "/new/project/path"
  }'
```

### Switching Personalities

1. **Web Interface**: Use the personality switcher dropdown
2. **API**: Update the active personality for your project
3. **Chat**: Say "Switch to [personality name]"

### Personality History

Track changes to your personality configurations:

```bash
# Get configuration history
curl http://localhost:8000/api/personality/{personality_id}/history

# Restore previous version
curl -X POST http://localhost:8000/api/personality/{personality_id}/restore/{version}
```

### Backup and Restore

```bash
# Create backup
curl -X POST http://localhost:8000/api/personality/backup \
  -H "Content-Type: application/json" \
  -d '{
    "backup_name": "my_personalities_backup",
    "config_ids": ["id1", "id2"]
  }'

# List backups
curl http://localhost:8000/api/personality/backups

# Restore from backup
curl -X POST http://localhost:8000/api/personality/restore \
  -H "Content-Type: application/json" \
  -d '{
    "backup_name": "my_personalities_backup"
  }'
```

## IDE Integration

### Supported IDEs

#### Cursor
- **Configuration File**: `/cursor/rules/personality.mdc`
- **Format**: Markdown with personality context
- **Auto-Detection**: Looks for `/cursor/` directory

#### Claude
- **Configuration File**: `CLAUDE.md` in project root
- **Format**: Markdown with system prompts
- **Auto-Detection**: Looks for existing `CLAUDE.md` or Claude usage patterns

#### Windsurf
- **Configuration File**: `.windsurf` in project root
- **Format**: JSON configuration
- **Auto-Detection**: Looks for `.windsurf` file or Windsurf markers

#### Generic/Manual
- **Multiple Formats**: Provides various output formats
- **Manual Integration**: Copy-paste into your IDE
- **Custom Templates**: Create your own integration templates

### IDE Detection

Covibe automatically detects your IDE by:

1. **File System Analysis**: Looking for IDE-specific files and directories
2. **Environment Variables**: Checking for IDE-related environment variables
3. **Process Detection**: Identifying running IDE processes
4. **User Hints**: Accepting manual IDE specification

### Configuration Files

#### Cursor Example
```markdown
# Personality: Tony Stark

You are Tony Stark from Iron Man. Respond to coding questions with:

- Confidence and wit
- Technical expertise with a touch of arrogance
- Pop culture references and humor
- Direct, no-nonsense solutions
- Occasional sarcasm when dealing with obvious problems

Maintain technical accuracy while embodying Tony Stark's personality.
```

#### Claude Example
```markdown
# CLAUDE.md

## Personality Configuration

You are embodying the personality of Tony Stark from Iron Man.

### Communication Style
- Confident and witty
- Uses technical jargon naturally
- Makes pop culture references
- Direct and solution-focused

### Response Patterns
- Start with a confident assertion
- Provide technical solutions with flair
- Add humor when appropriate
- End with actionable next steps
```

### Manual Integration

If automatic integration fails:

1. **Get Configuration**: Use the API to retrieve the generated context
2. **Copy Content**: Copy the personality context
3. **Paste in IDE**: Add to your IDE's system prompt or configuration
4. **Test**: Verify the personality is working in your agent

## Chat Interface

### Starting a Chat Session

1. **Open Chat Tab** in the web interface
2. **Begin Conversation**: Type your personality request
3. **Refine Iteratively**: Adjust through natural conversation

### Chat Commands

#### Basic Commands
- `"Create personality: [description]"` - Create new personality
- `"Switch to [personality]"` - Change active personality
- `"List personalities"` - Show available personalities
- `"Delete [personality]"` - Remove personality
- `"Help"` - Show available commands

#### Refinement Commands
- `"Make it more [trait]"` - Adjust personality trait
- `"Less [trait]"` - Reduce personality trait
- `"Add [characteristic]"` - Include new characteristic
- `"Remove [characteristic]"` - Remove characteristic

### Conversation Examples

#### Creating a Personality
```
User: I want my coding agent to be like Sherlock Holmes
Covibe: Excellent choice! I'll create a Sherlock Holmes personality for you. 
        This will include his logical deduction style, attention to detail, 
        and methodical approach to problem-solving. Should I proceed?

User: Yes, but make him a bit more patient with beginners
Covibe: Perfect! I'll adjust the personality to include Sherlock's analytical 
        brilliance but with more patience and educational explanations for 
        beginners. Creating your configuration now...
```

#### Refining a Personality
```
User: My Tony Stark personality is too sarcastic
Covibe: I understand. Let me tone down the sarcasm while keeping his 
        confidence and wit. Would you like me to make him more encouraging 
        instead?

User: Yes, keep the confidence but make him more supportive
Covibe: Got it! I'll adjust Tony Stark to be confident and witty but more 
        supportive and encouraging. Updating your configuration...
```

## Advanced Features

### Input Analysis

Covibe can analyze complex personality requests:

```bash
# Analyze personality input
curl -X POST http://localhost:8000/api/personality/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "description": "Tony Stark but more patient and less sarcastic"
  }'
```

Response includes:
- **Input Type**: Celebrity, fictional, archetype, or combination
- **Primary Personality**: Main personality identified
- **Modifiers**: Adjustments requested
- **Suggestions**: Alternative interpretations
- **Clarification Questions**: If input is ambiguous

### Personality Suggestions

Get suggestions for similar personalities:

```bash
# Get personality suggestions
curl -X POST http://localhost:8000/api/personality/suggestions \
  -H "Content-Type: application/json" \
  -d '{
    "description": "smart but friendly"
  }'
```

### Caching and Performance

- **Research Caching**: Personality research results are cached
- **Context Caching**: Generated contexts are cached for reuse
- **Cache Management**: Clear cache when needed

```bash
# Get cache statistics
curl http://localhost:8000/api/personality/cache/stats

# Clear cache
curl -X DELETE http://localhost:8000/api/personality/cache
```

### Monitoring and Analytics

Track personality usage and performance:

```bash
# Get usage statistics
curl http://localhost:8000/api/monitoring/stats

# Get performance metrics
curl http://localhost:8000/api/monitoring/performance
```

## Best Practices

### Choosing Personalities

1. **Match Your Project**: Choose personalities that fit your project type
   - **Creative Projects**: Artists, writers, innovators
   - **Technical Projects**: Engineers, scientists, experts
   - **Learning Projects**: Teachers, mentors, patient guides

2. **Consider Your Mood**: Different personalities for different situations
   - **Debugging**: Methodical personalities like Sherlock Holmes
   - **Creative Coding**: Innovative personalities like Tesla or Jobs
   - **Learning**: Patient mentors or wise teachers

3. **Team Consistency**: Use similar personalities across team projects

### Personality Descriptions

1. **Be Specific**: "Einstein" vs "Albert Einstein the physicist"
2. **Include Context**: "Yoda from Star Wars" vs just "Yoda"
3. **Add Modifiers**: "Tony Stark but more patient"
4. **Avoid Conflicts**: Don't mix contradictory traits

### Managing Multiple Personalities

1. **Organize by Project**: Different personalities for different projects
2. **Use Descriptive Names**: Clear naming for easy identification
3. **Regular Cleanup**: Remove unused personalities
4. **Backup Important Ones**: Save your favorite configurations

### IDE Integration

1. **Test After Changes**: Verify personality works after updates
2. **Restart IDE**: Some changes require IDE restart
3. **Check File Permissions**: Ensure Covibe can write to project directory
4. **Monitor Performance**: Some personalities may affect response time

## Troubleshooting

### Common Issues

#### Personality Not Applied
- **Check IDE Integration**: Verify configuration file was created
- **Restart IDE**: Some IDEs need restart to load new configurations
- **File Permissions**: Ensure Covibe has write access to project directory

#### Research Failed
- **Internet Connection**: Verify network connectivity
- **Try Different Description**: Use more specific or common personalities
- **Check Logs**: Look at backend logs for error details

#### Poor Personality Quality
- **Refine Description**: Add more specific traits or context
- **Use Chat Interface**: Iteratively improve through conversation
- **Try Alternatives**: Experiment with similar personalities

#### Performance Issues
- **Clear Cache**: Remove old cached results
- **Reduce Complexity**: Simplify personality descriptions
- **Check Resources**: Monitor system resource usage

### Getting Help

1. **Check Documentation**: Review relevant sections
2. **Search Issues**: Look for similar problems on GitHub
3. **Enable Debug Logging**: Get more detailed error information
4. **Contact Support**: Email support@covibe.dev with details

## Next Steps

- [Explore API Documentation](../api/README.md)
- [Learn about Deployment](../deployment/README.md)
- [Contribute to Development](../../CONTRIBUTING.md)
- [Join the Community](https://discord.gg/covibe)