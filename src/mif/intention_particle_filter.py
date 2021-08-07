import numpy as np
from src.mif.intention_application_interface import IntentionApplicationInterface

class IntentionParticleFilter:

    def __init__(
        self,
        num_intentions: int,
        num_particles_per_intention: int,
        intention_application_interface: IntentionApplicationInterface,
    ):
        """
        A generic intention particle filter, which has particles with intention hypotheses.

        Initialize intention particles. Note variables related to particles (e.g. self.intention, 
        self.intention_mask, self.weight, self.x_est) have the same order of particle indices in the 
        dimension of num_particles.
        
        Inputs:
            - num_intentions: Number of intentions.
            - num_particles_per_intention: Number of particles per intention.
            - intention_application_interface: Interface between application and intention particle filter.
        
        Updated:
            - self.num_intentions
            - self.num_particles
            - self.intention: numpy. :math:`(num_particles,)` Intention hypotheses for all particles. 
            e.g. for num_intentions=3, num_particles_per_intention=5, self.intention = 
            array([0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 2, 2, 2, 2, 2]).
            - self.intention_application_interface
            - self.x_est: list of length :math:`num_particles` or None. The state estimates of particles. 
            - self.intention_mask: numpy. :math:`(num_intentions, num_particles)` Mask on intention 
            hypotheses of all particles.
            e.g. for self.intention = array([0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 2, 2, 2, 2, 2]),
            self.intention_mask = \n
            array([[ True,  True,  True,  True,  True, False, False, False, False, False, False, False, False, False, False],\n
                    [False, False, False, False, False,  True,  True,  True,  True,  True, False, False, False, False, False],\n
                    [False, False, False, False, False, False, False, False, False, False,  True,  True,  True,  True,  True]])
            - self.weight: numpy. :math:`(num_particles,)` Particle weights. e.g. for num_particles=10,
            self.weight = array([0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1])
        
        Outputs:
            - None
        """
        self.num_intentions = num_intentions
        self.num_particles = self.num_intentions * num_particles_per_intention
        self.intention = np.arange(self.num_intentions).reshape(-1, 1).dot(\
            np.ones(num_particles_per_intention).reshape(1,-1)).reshape(-1).astype(int)
        self.intention_application_interface = intention_application_interface
        self.x_est = self.intention_application_interface.initialize_x() # ! todo general method # list with length of num_particles (maybe None in initialization.)
        self.intention_mask = self.create_intention_mask()
        self.reset_weights()

    def create_intention_mask(self):
        """
        Transform the updated intention indices to mask on intentions.

        Inputs:
            - None

        Updated:
            - None

        Outputs:
            - intention_mask: numpy. :math:`(num_intentions, num_particles)` Mask on intention hypotheses 
            of all particles. e.g. for self.intention = array([0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 2, 2, 2, 2, 2]),
            intention_mask = \n
            array([[ True,  True,  True,  True,  True, False, False, False, False, False, False, False, False, False, False],\n
                    [False, False, False, False, False,  True,  True,  True,  True,  True, False, False, False, False, False],\n
                    [False, False, False, False, False, False, False, False, False, False,  True,  True,  True,  True,  True]])
        """
        extended_intention = self.intention * np.ones((self.num_intentions, self.num_particles))
        extended_indices = np.arange(self.num_intentions)[:,np.newaxis] * \
            np.ones((self.num_intentions, self.num_particles))
        intention_mask = (extended_intention==extended_indices)
        return intention_mask

    def reset_weights(self):
        """
        Set the particle weights as uniform weights.

        Inputs:
            - None

        Updated:
            - self.weight: numpy. :math:`(num_particles,)` Particle weights. e.g. for 
            num_particles=10, weight = array([0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1])

        Outputs:
            - None
        """
        self.weight = np.ones(self.num_particles) * (1./self.num_particles)
        return
    
    def predict(self):
        """
        Propagate state estimates forward if there is any.

        Inputs:
            - None
        
        Updated:
            - self.x_est

        Outputs:
            - None
        """
        self.x_est = self.intention_application_interface.propagate_x(self.x_est, \
            self.intention, self.intention_mask)
        return
    

    def update_weight(self, x_obs, tau=0.1):
        """
        Update particle weights given the up-to-date observation.  The particle weight gets higher if the 
        gap between the observation and the estimate from that particle is lower.

        Inputs:
            - x_obs: Observation. The type changes according to the application.

        Updated:
            - self.weight

        Outputs:
            - None
        """
        gap = self.intention_application_interface.compare_observation(self.x_est, x_obs) # ! todo general method # (num_particles,)
        self.weight *= np.exp(-tau*gap)
        self.weight /= self.weight.sum()
        return

    def resample(self):
        """
        Sequential importance resampling (SIR): Resample particles according to current particle weights.
        Weights of resampled particles are reset.
        
        Inputs:
            - None
        
        Updated:
            - self.intention
            - self.intention_mask
            - self.weight
        
        Outputs:
            - None
        """
        resampled_indices = np.random.choice(self.num_particles, size=self.num_particles, p=self.weight)
        self.intention = self.intention[resampled_indices]
        self.intention_mask = self.create_intention_mask()
        self.x_est = self.intention_application_interface.resample_x(resampled_indices) # ! todo general method
        self.reset_weights()
        return
    
    def mutate(self, mutation_prob=0.01):
        """
        Mutate intention hypotheses of particles with a small probability. e.g. num_intentions=3, 
        mutation_prob=0.01, one particle's current intention is 0, the chance of the intention being 
        mutated is 0.01, where there is 0.005 chance converted to intention 1, and 0.005 chance converted 
        to intention 2.

        Inputs:
            - mutation_prob: Mutation probability.

        Updated:
            - self.intention
            - self.intention_mask

        Outputs:
            - None
        """
        mutation_mask_prob = 1.-mutation_prob*self.num_intentions/(self.num_intentions-1.)
        mutation_mask = np.random.uniform(size=self.num_particles) > mutation_mask_prob
        self.intention = self.intention * (1-mutation_mask) \
            + np.random.randint(0,self.num_intentions,self.num_particles) * mutation_mask
        self.intention = self.intention.astype(int)
        self.intention_mask = self.create_intention_mask()
        return
    
    def get_intention_probability(self):
        """
        Get probability distribution over intentions given current particle weights.

        Inputs:
            - None

        Updated:
            - None

        Outputs:
            - intention_prob_dist: numpy. :math:`(num_intentions,)` probability distribution over intentions.
        """
        intention_prob_dist = (self.weight * self.intention_mask).sum(axis=1)
        return intention_prob_dist


"""
comments for pedestrian application
    - intention_mean
    - num_intentions
        the number of intentions.
    - num_particles_per_intention
        the number of particles set for each intention.
    - num_tpp (default: 12)
        number of trajectory points for prediction.

    # self.intention_sampler = intention_sampler
    # self.intention_coordinates = self.intention_sampler.intent_bottom_left_coordinates + self.intention_sampler.intent_wid
    # self.num_tpp = num_tpp
    # intention_sampler,
    # num_tpp=12,
    # if self.args.intention_application == 'pedestrian': 
    #     self.intention_application_interface = PedestrianIntentionApplicationInterface(args)


# oe = self.x_pred - x_pred_true[np.newaxis]# offset error (particle_num, num_tpp, 2)
# aoe = np.mean(np.linalg.norm(oe, axis=2), axis=1) # (particle_num,) # ! gap is aoe
# self.weight *= np.exp(-tau*aoe)
# self.weight /= self.weight.sum()


    # def predict(self, x_obs, pred_func):
    #     self.goals = self.intention2goal()
    #     self.x_pred, _ = pred_func(x_obs, self.goals, self.intention, self.intention_coordinates, num_intentions=self.num_intentions, num_tpp=self.num_tpp)
    #     return self.x_pred
    
    # def predict_till_end(self, x_obs, long_pred_func):
    #     self.goals = self.intention2goal()
    #     _, infos = long_pred_func(x_obs, self.goals, self.intention, self.intention_coordinates,  num_intentions=self.num_intentions, num_tpp=self.num_tpp)
    #     return infos

    def particle_weight_intention_prob_dist(self):
        ### soft weight ###
        # weight_balanced = np.log(self.weight+params.WEIGHT_EPS) - np.log(min(self.weight+params.WEIGHT_EPS)) + 1. # (no zero in it is convenient for sampling)
        # weight_balanced /= sum(weight_balanced)
        ### original weight ###
        weight_balanced = self.weight
        particle_weight = [] # list of num_intentions (3) lists
        particle_weight_with_zero = self.weight * self.intention_mask# (particle_num,) * (num_intentions, particle_num) -> (num_intentions, particle_num)
        for intention_index in range(self.num_intentions):
            particle_weight_intention = particle_weight_with_zero[intention_index, particle_weight_with_zero[intention_index, :].nonzero()]
            particle_weight.append(np.squeeze(particle_weight_intention, axis=0))
        return particle_weight, (weight_balanced*self.intention_mask).sum(axis=1)
    
    def intention2goal(self):
        return self.intention_sampler.idx2intent_sampling(self.intention)
"""