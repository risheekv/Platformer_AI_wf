import pygame
import numpy as np
import tensorflow as tf
import os
from main import Chaser, screen_width, screen_height

def create_model():
    model = tf.keras.Sequential([
        tf.keras.layers.Dense(64, activation='relu', input_shape=(3,)),
        tf.keras.layers.Dense(32, activation='relu'),
        tf.keras.layers.Dense(2, activation='tanh')  # Output x,y movement
    ])
    model.compile(optimizer='adam', loss='mse')
    return model

def generate_training_data(num_samples=10000):
    print("Generating training data...")
    training_data = []
    
    # Generate various movement patterns
    for _ in range(num_samples):
        # Random movement pattern
        movement = np.random.normal(0, 0.5, 4)
        movement = np.clip(movement, -1, 1)
        training_data.append(movement)
        
        # Circular movement pattern
        angle = np.random.uniform(0, 2 * np.pi)
        movement = np.array([
            np.cos(angle),
            np.sin(angle),
            np.random.uniform(0.5, 1.0),
            np.sign(np.cos(angle))
        ])
        training_data.append(movement)
        
        # Direct chase pattern
        target = np.random.normal(0, 0.5, 2)
        direction = target / (np.linalg.norm(target) + 1e-8)
        movement = np.array([
            direction[0],
            direction[1],
            np.random.uniform(0.5, 1.0),
            np.sign(direction[0])
        ])
        training_data.append(movement)
        
        # Zigzag pattern
        zigzag = np.array([
            np.sin(_ * 0.1),
            np.cos(_ * 0.1),
            np.random.uniform(0.5, 1.0),
            np.sign(np.sin(_ * 0.1))
        ])
        training_data.append(zigzag)
        
        # Predictive chase pattern
        future_pos = np.random.normal(0, 0.5, 2)
        current_pos = np.random.normal(0, 0.5, 2)
        velocity = (future_pos - current_pos) / (np.linalg.norm(future_pos - current_pos) + 1e-8)
        movement = np.array([
            velocity[0],
            velocity[1],
            np.random.uniform(0.5, 1.0),
            np.sign(velocity[0])
        ])
        training_data.append(movement)
    
    return np.array(training_data)

def train_model(epochs=1000, batch_size=32, save_interval=100):
    # Initialize pygame
    pygame.init()
    screen = pygame.display.set_mode((screen_width, screen_height))
    pygame.display.set_caption('Chaser Training')
    
    # Create chaser instance
    chaser = Chaser(screen_width//2, screen_height//2)
    
    # Create and compile model
    model = create_model()
    
    # Generate training data
    training_data = generate_training_data()
    
    print(f"Starting training for {epochs} epochs...")
    print(f"Training data shape: {training_data.shape}")
    
    # Training loop
    for epoch in range(epochs):
        # Shuffle training data
        np.random.shuffle(training_data)
        
        total_loss = 0
        batches = 0
        
        # Train in batches
        for i in range(0, len(training_data), batch_size):
            batch = training_data[i:i + batch_size]
            if len(batch) == batch_size:  # Only use complete batches
                # Prepare input and target data
                X = batch[:, :3]  # State: dx, dy, distance
                y = batch[:, :2]  # Target: dx, dy movement
                
                # Train step
                loss = model.train_on_batch(X, y)
                total_loss += loss
                batches += 1
        
        # Calculate average loss
        avg_loss = total_loss / batches if batches > 0 else 0
        
        # Print progress
        if (epoch + 1) % 10 == 0:
            print(f"Epoch {epoch + 1}/{epochs}")
            print(f"Loss: {avg_loss:.4f}")
        
        # Save model periodically
        if (epoch + 1) % save_interval == 0:
            print(f"Saving model at epoch {epoch + 1}...")
            model.save('chaser_model.h5')
            
        # Visualize training
        screen.fill((255, 255, 255))
        
        # Generate and display some movements
        for _ in range(10):
            state = np.random.normal(0, 0.5, 3)
            state = np.clip(state, -1, 1)
            action = model.predict(np.array([state]), verbose=0)[0]
            
            start_x = np.random.randint(0, screen_width)
            start_y = np.random.randint(0, screen_height)
            end_x = int(start_x + action[0] * 50)
            end_y = int(start_y + action[1] * 50)
            
            # Draw movement line
            pygame.draw.line(screen, (0, 0, 255), 
                           (start_x, start_y), 
                           (end_x, end_y), 2)
            
            # Draw direction indicator
            pygame.draw.circle(screen, (255, 0, 0), 
                             (end_x, end_y), 5)
        
        pygame.display.flip()
        
        # Handle pygame events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return
    
    print("Training completed!")
    model.save('chaser_model.h5')
    pygame.quit()

if __name__ == "__main__":
    train_model() 