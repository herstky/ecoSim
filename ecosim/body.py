from random import uniform, randint

from ecosim.constants import *
from ecosim.neural_network import NeuralNetwork


class Nose:
    def __init__(self, particleThreshold=25):
        self.particleThreshold = particleThreshold

    def smell(self, animal, board, targetClass): 
        row, col = animal.coords
        size = 3
        scentMatrix = [[0 for i in range(size)] for j in range(size)]
        for y in range(size):
            for x in range(size):
                if board.validPosition((row + y - 1, col + x - 1)) and not board.cellContains(animal.coords, animal.__class__):
                    for particle in board[row + y - 1][col + x - 1].particles:
                        if particle.sourceClass == targetClass and particle.count >= self.particleThreshold:
                            scentMatrix[y][x] = particle.count 
                            break    
        return scentMatrix            
      
# TODO eyes should perceive edges of the map and visible entities in adjacent tiles
class Eyes:
    def __init__(self):
        pass

class Brain:
    def __init__(self):
        self.neuralNetwork = NeuralNetwork()

    def decide(self, inputs):
        return self.neuralNetwork.forwardPropagate(inputs)

    def mutate(self):
        for theta in self.neuralNetwork.weights:
            for row in range(len(theta)):
                for col in range(len(theta[0])):
                    if randint(1, 100) <= 3:
                        theta[row][col] = uniform(-1, 1)
                    variance = theta[row][col] * .05
                    theta[row][col] += uniform(-variance / 2, variance / 2)

    def inheritance(self, other):
        newWeights = []
        maxLayerDepth = max(len(self.neuralNetwork.weights), len(other.neuralNetwork.weights))
        for i in range(maxLayerDepth):
            newWeights.append([])
            if i >= len(self.neuralNetwork.weights):
                numNodes = len(other.neuralNetwork.weights[i])
            else:
                numNodes = len(self.neuralNetwork.weights[i])
            for j in range(numNodes):
                if j < len(self.neuralNetwork.weights[i]) and j < len(other.neuralNetwork.weights[i]):
                    if randint(1, 100) <= 50:
                        newWeights[i].append(self.neuralNetwork.weights[i][j])
                    else:
                        newWeights[i].append(other.neuralNetwork.weights[i][j])
                elif j < len(self.neuralNetwork.weights[i]):
                    newWeights[i].append(self.neuralNetwork.weights[i][j])
                elif j < len(other.neuralNetwork.weights[i]):
                    newWeights[i].append(other.neuralNetwork.weights[i][j])
        return newWeights




class Stomach:
    def __init__(self, body, capacityRatio=.2, digestionRate=.05):
        self.body = body
        self.contents = []
        self.capacityRatio = capacityRatio
        self.digestionRate = digestionRate # TODO FIX

    @property
    def capacity(self):
        return self.body.mass * self.capacityRatio
        
    @property
    def capacityRemaining(self):
        return self.capacity - self.contentsMass

    @property
    def contentsMass(self):
        mass = 0
        for bolus in self.contents:
            mass += bolus.body.mass
        return mass

    @property
    def digestionCapacity(self):
        return self.digestionRate * self.body.mass
    
    def consume(self, organism):
        edibleMass = organism.body.mass * organism.body.edibleMassFraction
        organism.body.mass = min(edibleMass, self.capacityRemaining) 
        self.contents.append(organism)

    def digest(self):
        amountDigested = 0
        energyGained = 0
        while amountDigested < self.digestionCapacity and self.contentsMass > 0:
            bolus = self.contents[0]
            changeInMass = min(self.digestionCapacity - amountDigested, bolus.body.mass)
            bolus.body.mass -= changeInMass
            if bolus.body.mass <= 0:
                self.contents.pop(0)
            amountDigested += changeInMass 
            energyGained += bolus.body.energyContent * changeInMass
        return energyGained - self.body.totalEnergyExpenditure
        

class Body:
    def __init__(self, mass=10, massCapacity=100):
        self.mass = mass
        self.massCapacity = massCapacity

    @property
    def edibleMassFraction(self):
        return 1

    @property
    def energyContent(self):
        return 1000

    
class AnimalBody(Body):
    def __init__(self, mass=50, massCapacity=70):
        super().__init__(mass, massCapacity)
        self.fatMassFraction = .20
        self.muscleMassFraction = .35
        self.fatStorageFraction = self.fatMassFraction / (self.fatMassFraction + self.muscleMassFraction)
        self.muscleStorageFraction = 1 - self.fatStorageFraction
        self.totalEnergyExpenditure = 0 # keeps track of the total amount of energy spent during current tick
        self.satiationThreshold = .6
        self.starvationThreshold = .05 # fatMassFraction dropping below this threshold causes death
        self.satiationAmount = 10
        self.stomach = Stomach(self)

    @property
    def edibleMassFraction(self):
        return self.fatMassFraction + self.muscleMassFraction

    @property
    def energyContent(self):
        fatProportion = self.fatMassFraction / self.edibleMassFraction
        muscleProportion = self.muscleMassFraction / self.edibleMassFraction
        return fatProportion * BODY_FAT_ENERGY_CONTENT + muscleProportion * BODY_MUSCLE_ENERGY_CONTENT

    def hungry(self):
        return self.stomach.contentsMass / self.stomach.capacity < self.satiationThreshold

    def eat(self, organism):
        self.stomach.consume(organism)

    def starved(self):
        return self.fatMassFraction < self.starvationThreshold

    def metabolize(self):
        netEnergy = self.stomach.digest()
        
        # energy is burned from or stored purely as fat if energy is lost or if fully grown
        if netEnergy < 0 or self.mass >= self.massCapacity: 
            massGained = netEnergy / BODY_FAT_ENERGY_CONTENT
            startingFatMass = self.mass * self.fatMassFraction
            self.mass += massGained
            self.fatMassFraction = (startingFatMass + massGained) / self.mass
        else: 
            startingMass = self.mass
            startingFatMass = self.mass * self.fatMassFraction
            startingMuscleMass = self.mass * self.muscleMassFraction
            massGained = netEnergy / (self.fatStorageFraction * BODY_FAT_ENERGY_CONTENT + self.muscleStorageFraction * BODY_MUSCLE_ENERGY_CONTENT)
            fatMassGained = massGained * self.fatStorageFraction 
            muscleMassGained = massGained * self.muscleStorageFraction 
            self.mass += massGained
            self.fatMassFraction = (startingFatMass + fatMassGained) / self.mass
            self.muscleMassFraction = (startingMuscleMass + muscleMassGained) / self.mass

    def canReproduce(self):
        return self.fatMassFraction >= .16

    # Resets the total energy expenditure to the baseline. This method should be called before 
    # any other energy expenditure calculations are done
    def baselineEnergyExpenditure(self):
        self.totalEnergyExpenditure = 5500 + 150 * self.mass

    # magnitude should be approximately 1 for moving a single space, 2-3 for chasing prey, etc
    def actionEnergyExpenditure(self, magnitude):
        self.totalEnergyExpenditure += 2000 + 80 * magnitude * self.mass


class PlantBody(Body):
    def __init__(self, mass=1, massCapacity=35):
        super().__init__(mass, massCapacity)
        self.growthRate = .4

    def grow(self):
        # mass added increases as plant grows, until massCapacity is reached
        if self.mass < self.massCapacity:
            self.mass += min(self.massCapacity, self.mass * self.growthRate)

    @property
    def edibleMassFraction(self):
        return 1

    @property
    def energyContent(self):
        return WHEAT_GRASS_ENERGY_CONTENT