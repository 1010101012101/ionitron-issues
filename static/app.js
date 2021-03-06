angular.module('app', ['ui.router', 'ngGrid'])

.config(function($stateProvider, $urlRouterProvider) {

  $stateProvider

    .state('manage', {
      url: '/manage',
      templateUrl: '/partials/manage.html',
      controller: 'AppCtrl',
    })

    .state('issues', {
      url: '/:repo_username/:repo_id',
      templateUrl: '/partials/issues.html',
      controller: 'IssueListCtrl',
    })

    .state('index', {
      url: '/',
      templateUrl: '/partials/index.html',
      controller: 'AppIndex'
    });

  $urlRouterProvider.otherwise('/');

})


.controller('AppCtrl', function($scope, $http){

    $scope.response = {'text': 'Nothing to show. Click below to manually trigger a cron task.'};

    $scope.manualCron = function(location){
      $scope.response.text = 'Making request. This might take a while...';
      $http.get('/api/' + location)
        .success(function(data){
          $scope.response.text = JSON.stringify(data);
        })
        .error(function(data){
          $scope.response.text = JSON.stringify(data);
        });
    };
})

.controller('IssueListCtrl', function($scope, $location, ScoreFactory, $stateParams){

    $scope.isLoading = true;
    $scope.issue_data = [];

    $scope.gridOptions = {
        data: 'issue_data',
        sortInfo: { fields: ['score'], directions: ['desc']},
        columnDefs: [
          {field: 'rank', displayName:'Rank', width: '4%', cellFilter: 'number:0'},
          {field: 'score', displayName:'Score', width: '5%', cellFilter: 'number:0',
                      cellTemplate: '<div class="ngCellText"  title="{{row.getProperty(\'score_data\') | scoreData}}"><span ng-cell-text>{{row.getProperty(col.field)}}</span></div>'},
          {field: 'number', displayName:'Issue #', width:'5%',
                      cellTemplate: '<div class="ngCellText"><a href="{{repo_data.repo_url}}/issues/{{row.getProperty(col.field)}}" target="_blank">#<span ng-cell-text>{{row.getProperty(col.field)}}</span></a></div>'},
          {field: 'comments', displayName:'Comments', width: '6%', cellFilter: 'number:0'},
          {field: 'references', displayName:'Refs', width: '3%', cellFilter: 'number:0'},
          {field: 'created', displayName: 'Created', width: '6%', cellFilter: 'date:"MM/dd/yy"'},
          {field: 'updated', displayName: 'Updated', width: '6%', cellFilter: 'date:"MM/dd/yy"'},
          {field: 'username', displayName:'User', width: '11%', cellTemplate: '<div class="ngCellText"><img class="thumb" ng-src="{{row.getProperty(\'avatar\')}}"><a href="http://github.com/{{row.getProperty(col.field)}}" target="_blank"><span ng-cell-text>{{row.getProperty(col.field)}}</span></a></div>'},
          {field: 'title', displayName: 'Title', width: '40%', cellTemplate: '<div class="ngCellText"><strong ng-if="row.getProperty(\'pull_request\')">PR: </strong><span ng-cell-text>{{row.getProperty(col.field)}}</span></div>'},
          {field: 'assignee', displayName: 'Assignee', width: '8%'},
          {field: 'milestone', displayName: 'Milestone', width: '6%'},
        ],
        multiSelect: false,
        afterSelectionChange: afterSelectionChange
    };

    function afterSelectionChange(rowItem, event) {
      if (!rowItem.selected) return;
      $scope.issueDetail = angular.copy(rowItem.entity);
      $scope.issueDetail.actionType = 'close';
      $scope.issueDetail.messageType = '';
      console.log($scope.issueDetail);
    }

    $scope.submit = function() {
      $scope.issueDetail.error = null;

      if (!$scope.issueDetail.actionType || !$scope.issueDetail.messageType) {
        return;
      }

      $scope.issueDetail.isDisabled = true;

      ScoreFactory.submitResponse($scope.issueDetail.repo_username, $scope.issueDetail.repo_id, $scope.issueDetail.number, $scope.issueDetail.actionType, $scope.issueDetail.messageType, $scope.issueDetail.customMessage).then(function(data){
        if (data.error) {
          $scope.issueDetail.error = data.error;
          $scope.issueDetail.isDisabled = false
          return;
        }

        if (data.issue_closed) {
          for (var x = 0; x < $scope.issue_data.length; x++) {
            if ($scope.issue_data[x].number == $scope.issueDetail.number) {
              $scope.issue_data.splice(x, 1);
              break;
            }
          }
        }

        $scope.issueDetail = null;
        console.log('submit response');
      });
    };

    ScoreFactory.fetchRepoIssues($stateParams.repo_username, $stateParams.repo_id).then(function(data){
      $scope.isLoading = false;
      $scope.repo_data = data;
      $scope.issue_data = data.issues;
      $scope.errorMsg = data.error;
    });

})

.controller('AppIndex', function($scope, $location, $state, ScoreFactory){
  var organization = 'driftyco';

  $scope.isLoading = true;
  $scope.repos = [];

  $scope.gridOptions = {
      data: 'repos',
      sortInfo: { fields: ['open_issues_count'], directions: ['desc']},
      columnDefs: [
        {field: 'name', displayName: 'Repo', width: '20%'},
        {field: 'open_issues_count', displayName: 'Issues', width: '20%', cellFilter: 'number:0'},
        {field: 'stargazers_count', displayName: 'Stars', width: '20%', cellFilter: 'number:0'},
      ],
      multiSelect: false,
      afterSelectionChange: afterSelectionChange
  };

  function afterSelectionChange(rowItem) {
    if (!rowItem.selected) return;

    $state.go('issues', {
      'repo_username': organization,
      'repo_id': rowItem.entity.name
    });
  }

  ScoreFactory.fetchRepos(organization).then(function(data) {
    $scope.repos = data.repos;
    $scope.isLoading = false;
  });

})

.factory('ScoreFactory', function($http, $q){

  return {

    fetchRepoIssues: function(repo_username, repo_id) {
      var deferred = $q.defer();
      var url = '/api/' + repo_username + '/' + repo_id + '/issue-scores';

      $http.get(url)
        .success(function(data, status, headers, config) {
          deferred.resolve(data);
        })
        .error(function(data, status, headers, config) {
          deferred.reject(data);
        });
        return deferred.promise;
    },

    fetchRepos: function(repo_username) {
      var deferred = $q.defer();
      var url = '/api/' + repo_username + '/repos';

      $http.get(url)
        .success(function(data, status, headers, config) {
          deferred.resolve(data);
        })
        .error(function(data, status, headers, config) {
          deferred.reject(data);
        });
        return deferred.promise;
    },

    submitResponse: function(repo_username, repo_id, number, actionType, messageType, customMessage) {
      var deferred = $q.defer();

      $http.post('/api/' + repo_username + '/' + repo_id + '/' + number + '/issue-response', {
        'action_type': actionType,
        'message_type': messageType,
        'custom_message': customMessage
      })
        .success(function(data, status, headers, config) {
          deferred.resolve(data);
        })
        .error(function(data, status, headers, config) {
          deferred.reject(data);
        });
        return deferred.promise;
    }

  }

})

.directive('stopEvent', function () {
    return {
        restrict: 'A',
        link: function (scope, element, attr) {
            element.bind('click', function (e) {
                e.stopPropagation();
            });
        }
    };
})

.filter('scoreData', function() {
  return function(scoreData) {
    var sortable = [];
    for (var n in scoreData) {
      sortable.push([n, scoreData[n]]);
    }
    sortable.sort(function(a, b) {return a[1] - b[1]}).reverse();

    var out = [];
    for (var x = 0; x < sortable.length; x++) {
      out.push(sortable[x][1] + ' - ' + sortable[x][0]);
    }

    return out.join('\n');
  };
})
